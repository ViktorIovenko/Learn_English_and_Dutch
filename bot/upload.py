# bot/upload.py
# Импорт слов из CSV + кнопки подтверждения
# [ИЗМЕНЕНО v4.29] Добавлена защита от конфликтов нумерации уроков:
#                  автоматическая перенумерация уроков файла в диапазон (max_урок_в_БД + 1 ...),
#                  при этом вторая часть номера (индекс слова) сохраняется.
#                  Отчёт дополняется картой переназначения уроков.
# [ИЗМЕНЕНО v4.28] «Подтвердите импорт» тоже автоудаляется; «Меню» всегда одно — старое удаляем.
# [ИЗМЕНЕНО v4.27] Кнопки подтверждения показываются сразу после парсинга.

import os
import tempfile
import sqlite3
import asyncio
import re  # ← [ДОБАВЛЕНО v4.29]
from typing import List, Dict, Tuple
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import Config
from bot.db import is_user_registered, bulk_upsert_words
from bot.validators import parse_csv_to_rows, validate_example_usage, expected_word_for
from bot.auth import get_persistent_keyboard, show_menu_with_keyboard  # ← ИЗМЕНЕНО: новый хелпер

EPHEMERAL_SECONDS = 20.0

def _norm_nl(nl: str) -> str: return (nl or "").strip().lower()

def _get_existing_nl_set(db_path: str) -> set[str]:
    existing = set()
    try:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor(); cur.execute("SELECT nl FROM words")
            for (nl,) in cur.fetchall(): existing.add(_norm_nl(nl))
        finally:
            conn.close()
    except Exception:
        pass
    return existing

# ---------------- [ДОБАВЛЕНО v4.29] ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ НУМЕРАЦИИ ----------------

_NUM_RE = re.compile(r'^\s*(\d+)(?:\.(\d+))?')

def _parse_number(num: str) -> Tuple[int|None, int|None]:
    """
    Разбирает строку вида 'L.W' → (L, W). Если нет точки — (L, None).
    При неуспехе возвращает (None, None).
    """
    if not num:
        return None, None
    m = _NUM_RE.match(str(num))
    if not m:
        return None, None
    l = int(m.group(1))
    w = int(m.group(2)) if m.group(2) is not None else None
    return l, w

def _get_db_lessons_set_and_max(db_path: str) -> Tuple[set[int], int]:
    """
    Считывает столбец number из таблицы words и вытаскивает из него номера уроков (часть до '.').
    Возвращает (множество уроков, максимальный урок) — если пусто, max=0.
    """
    lessons = set()
    max_lesson = 0
    try:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            try:
                cur.execute("SELECT number FROM words")
            except Exception:
                # Если столбца number нет, считаем что уроков нет
                return set(), 0
            for (num_str,) in cur.fetchall():
                L, _ = _parse_number(num_str)
                if L is not None:
                    lessons.add(L)
                    if L > max_lesson:
                        max_lesson = L
        finally:
            conn.close()
    except Exception:
        pass
    return lessons, max_lesson

def _format_lesson_remap(mapping: Dict[int, int]) -> str:
    if not mapping:
        return ""
    lines = ["🔢 Перенумерация уроков:"]
    for old in sorted(mapping.keys()):
        lines.append(f" - Урок {old} → {mapping[old]}")
    return "\n".join(lines)

def _renumber_lessons_if_needed(rows: List[Dict[str, str]], db_path: str) -> Tuple[List[Dict[str, str]], Dict[int, int]]:
    """
    Проверяет конфликт нумерации уроков между файлом и БД.
    Если любой урок из файла уже есть в БД ИЛИ <= max_урок_в_БД — перенумеровывает
    ВСЕ уникальные уроки из файла в новый непрерывный диапазон, начиная с max+1.
    ВТОРАЯ часть номера (индекс слова) сохраняется без изменений.
    Возвращает (обновлённые rows, карта {старый_урок: новый_урок}).
    """
    if not rows:
        return rows, {}

    db_lessons, db_max = _get_db_lessons_set_and_max(db_path)

    # Собираем уникальные уроки в порядке появления
    file_lessons_order: List[int] = []
    file_lessons_set: set[int] = set()
    for r in rows:
        L, _ = _parse_number(r.get("number", "") or "")
        if L is None:
            continue
        if L not in file_lessons_set:
            file_lessons_set.add(L)
            file_lessons_order.append(L)

    if not file_lessons_order:
        # В файле нет корректных номеров — ничего не делаем
        return rows, {}

    # Условие перенумерации:
    # 1) пересечение с уже существующими уроками в БД, или
    # 2) любой номер урока в файле <= db_max (чтобы «продолжать» только вперёд)
    conflict = any((L in db_lessons) or (L <= db_max) for L in file_lessons_order)

    if not conflict:
        return rows, {}  # уже «свежие» номера — оставляем как есть

    # Строим отображение: старые уроки файла → новые, начиная с db_max + 1
    mapping: Dict[int, int] = {}
    next_lesson = db_max + 1
    for L in file_lessons_order:
        mapping[L] = next_lesson
        next_lesson += 1

    # Применяем перенумерацию к строкам
    new_rows: List[Dict[str, str]] = []
    for r in rows:
        num = r.get("number", "") or ""
        L, W = _parse_number(num)
        if L is None:
            new_rows.append(r)
            continue
        new_L = mapping.get(L, L)
        # Если W отсутствовал — сохраняем «L.»; если был — «L.W»
        new_number = f"{new_L}.{W}" if W is not None else f"{new_L}."
        rr = dict(r)
        rr["number"] = new_number
        new_rows.append(rr)

    return new_rows, mapping

# ------------------------------------------------------------------------------------------

def _format_full_list(items: List[tuple], header_emoji: str, header_text: str) -> str:
    if not items: return ""
    lines = [f"{header_emoji} {header_text}: {len(items)}"]
    for n, w in items:
        n = n if n is not None else "?"
        w = w if w is not None else ""
        lines.append(f" - {n} ({w})")
    return "\n".join(lines)

async def _delete_user_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update and update.message:
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    except Exception: pass

async def _delete_later(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: float = EPHEMERAL_SECONDS):
    await asyncio.sleep(delay)
    try: await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception: pass

async def _send_long(update: Update, text: str, chunk_limit: int = 3500) -> List[int]:
    sent_ids: List[int] = []
    if len(text) <= chunk_limit:
        m = await update.effective_chat.send_message(text); sent_ids.append(m.message_id); return sent_ids
    parts, acc, acc_len = [], [], 0
    for line in text.splitlines():
        ln = len(line) + 1
        if acc_len + ln > chunk_limit and acc:
            parts.append("\n".join(acc)); acc, acc_len = [line], ln
        else:
            acc.append(line); acc_len += ln
    if acc: parts.append("\n".join(acc))
    for p in parts:
        m = await update.effective_chat.send_message(p); sent_ids.append(m.message_id)
    return sent_ids

def _filter_duplicates_by_nl(rows: List[Dict[str, str]], db_path: str):
    existing_db = _get_existing_nl_set(db_path)
    seen_in_file = set(); filtered = []; skipped_in_file = []; skipped_in_db = []
    for r in rows:
        nl = _norm_nl(r.get("nl", ""))
        if not nl:
            filtered.append(r); continue
        if nl in seen_in_file:
            skipped_in_file.append((r.get("number", "?"), r.get("nl", ""))); continue
        if nl in existing_db:
            skipped_in_db.append((r.get("number", "?"), r.get("nl", ""))); continue
        seen_in_file.add(nl); filtered.append(r)
    return filtered, skipped_in_file, skipped_in_db

# ---------------- ХЕНДЛЕРЫ ----------------
async def cmd_upload_words(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await _delete_user_trigger(update, context)
    await show_menu_with_keyboard(update, context, user.id)   # ← ИЗМЕНЕНО

    if not is_user_registered(Config.DB_PATH, user.id):
        m = await update.effective_chat.send_message("Сначала пройдите регистрацию: отправьте /start и введите пароль.")
        asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))
        return

    pending = context.user_data.get("pending_import_all") or []
    if pending:
        kb_confirm = ReplyKeyboardMarkup(
            [["Импортировать как есть", "Отменить импорт"]],
            resize_keyboard=True, is_persistent=True, one_time_keyboard=False
        )
        m = await update.effective_chat.send_message("Подтвердите импорт:", reply_markup=kb_confirm)
        asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))  # ← ИЗМЕНЕНО: удаляем подсказку
        return

    m = await update.effective_chat.send_message(
        ("📥 <b>Загрузите .csv файл со словами</b>\n\n"
         "Перед загрузкой посмотрите пример структуры таблицы:\n"
         '<a href="https://docs.google.com/spreadsheets/d/1OBKebdrOGZMcT00Yq_RfB9FuyCIc8QBHoRmluuGpwr4/edit?usp=sharing">📄 Образец CSV таблицы</a>'),
        parse_mode="HTML", disable_web_page_preview=True
    )
    asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))

async def on_csv_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await _delete_user_trigger(update, context)
    await show_menu_with_keyboard(update, context, user.id)   # ← ИЗМЕНЕНО

    if not is_user_registered(Config.DB_PATH, user.id):
        m = await update.effective_chat.send_message("Сначала пройдите регистрацию: отправьте /start и введите пароль.")
        asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))
        return

    doc = update.message.document
    if not doc: return
    fname = (doc.file_name or "").lower()
    if not (fname.endswith(".csv") or (doc.mime_type and "csv" in doc.mime_type.lower())):
        m = await update.effective_chat.send_message("Это не .csv файл. Пожалуйста, пришлите CSV.")
        asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))
        return

    tmpdir = tempfile.mkdtemp(prefix="csv_upload_")
    tmp_path = os.path.join(tmpdir, fname or "words.csv")
    file = await context.bot.get_file(doc.file_id); await file.download_to_drive(custom_path=tmp_path)

    try:
        all_rows: List[Dict[str, str]] = parse_csv_to_rows(tmp_path)
        # Фильтруем дубль-слова заранее
        filtered_rows, skipped_in_file, skipped_in_db = _filter_duplicates_by_nl(all_rows, Config.DB_PATH)

        if not filtered_rows:
            blocks = ["⚠ Все загруженные слова уже есть (или повторяются в файле) и были пропущены."]
            if skipped_in_file: blocks.append(_format_full_list(skipped_in_file, "🔁", "Повторы внутри файла"))
            if skipped_in_db:   blocks.append(_format_full_list(skipped_in_db, "📚", "Уже были в базе"))
            ids = await _send_long(update, "\n\n".join(blocks))
            for mid in ids: asyncio.create_task(_delete_later(context, update.effective_chat.id, mid))
            return

        # ---------- [ДОБАВЛЕНО v4.29] Защита нумерации уроков ----------
        filtered_rows, remap = _renumber_lessons_if_needed(filtered_rows, Config.DB_PATH)
        # ---------------------------------------------------------------

        _, bad_rows = validate_example_usage(filtered_rows)
        context.user_data["pending_import_all"] = filtered_rows

        # 1) Кнопки подтверждения — сразу и тоже удалим через 20 сек (клавиатура останется)
        kb_confirm = ReplyKeyboardMarkup(
            [["Импортировать как есть", "Отменить импорт"]],
            resize_keyboard=True, is_persistent=True, one_time_keyboard=False
        )
        m = await update.effective_chat.send_message("Подтвердите импорт:", reply_markup=kb_confirm)
        asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))  # ← ИЗМЕНЕНО

        # 2) Отчёт — отдельно, самоуничтожится
        extra_blocks = []
        if remap:            extra_blocks.append(_format_lesson_remap(remap))        # ← [ДОБАВЛЕНО v4.29]
        if skipped_in_file:  extra_blocks.append(_format_full_list(skipped_in_file, "🔁", "Пропущены повторы внутри файла"))
        if skipped_in_db:    extra_blocks.append(_format_full_list(skipped_in_db, "📚", "Пропущены как уже существующие в базе"))

        if bad_rows:
            tip_lines = []
            for b in bad_rows[:30]:
                parts = []
                for fld in b["missing"]:
                    parts.append(f"{fld}: «{expected_word_for(fld, b)}»")
                tip_lines.append(f"{b['number']}: " + "; ".join(parts))
            more = f"\n... и ещё {len(bad_rows) - 30} строк(и)." if len(bad_rows) > 30 else ""
            head = "⚠ Обнаружены строки, где слово не встречается в своём примере."
            body = ("\n".join(tip_lines) + more) if tip_lines else "Нет подробностей по строкам."
            tail = "\n\n".join(extra_blocks) if extra_blocks else ""
            msg = f"{head}\n\n{body}" + (f"\n\n{tail}" if tail else "")
        else:
            head = "⚙ Проверка завершена, ошибок не найдено."
            tail = ("\n\n" + "\n\n".join(extra_blocks)) if extra_blocks else ""
            msg = f"{head}\nНайдено строк к импорту: {len(filtered_rows)}{tail}"

        ids = await _send_long(update, msg + "\n\nВыберите действие ниже.")
        for mid in ids: asyncio.create_task(_delete_later(context, update.effective_chat.id, mid))
        return

    except Exception as e:
        m = await update.effective_chat.send_message(f"❌ Ошибка импорта: {e}")
        asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))

async def on_confirm_import_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await _delete_user_trigger(update, context)

    rows: List[Dict[str, str]] = context.user_data.get("pending_import_all") or []

    # Сразу вернём «меню» (это уберёт клавиатуру подтверждения) — старое меню удалится само
    await show_menu_with_keyboard(update, context, user.id)   # ← ИЗМЕНЕНО

    if not rows:
        m = await update.effective_chat.send_message("Нет данных к импорту. Пришлите CSV снова.")
        asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))
        return

    m = await update.effective_chat.send_message("⏳ Импортирую...")
    asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))

    # Повторная защита: если pending появился до обновления — всё равно перенумеруем при необходимости
    rows2, remap = _renumber_lessons_if_needed(rows, Config.DB_PATH)  # ← [ДОБАВЛЕНО v4.29]

    filtered_rows, skipped_in_file, skipped_in_db = _filter_duplicates_by_nl(rows2, Config.DB_PATH)
    if not filtered_rows:
        blocks = ["⚠ Все загруженные слова уже есть (или повторяются в файле) и были пропущены."]
        if skipped_in_file: blocks.append(_format_full_list(skipped_in_file, "🔁", "Внутри файла повторов"))
        if skipped_in_db:   blocks.append(_format_full_list(skipped_in_db, "📚", "Уже были в базе"))
        if remap:           blocks.append(_format_lesson_remap(remap))  # ← [ДОБАВЛЕНО v4.29]
        ids = await _send_long(update, "\n\n".join(blocks))
        for mid in ids: asyncio.create_task(_delete_later(context, update.effective_chat.id, mid))
        context.user_data.pop("pending_import_all", None)
        return

    count = bulk_upsert_words(Config.DB_PATH, filtered_rows)
    context.user_data.pop("pending_import_all", None)

    blocks = [f"✅ Импортировано записей (после фильтра дублей): {count}"]
    if remap:           blocks.append(_format_lesson_remap(remap))      # ← [ДОБАВЛЕНО v4.29]
    if skipped_in_file: blocks.append(_format_full_list(skipped_in_file, "🔁", "Пропущены повторы внутри файла"))
    if skipped_in_db:   blocks.append(_format_full_list(skipped_in_db, "📚", "Уже были в базе"))
    ids = await _send_long(update, "\n\n".join(blocks))
    for mid in ids: asyncio.create_task(_delete_later(context, update.effective_chat.id, mid))

async def on_cancel_import(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await _delete_user_trigger(update, context)

    # Возвращаем «меню» (и тем самым убираем клавиатуру подтверждения)
    await show_menu_with_keyboard(update, context, user.id)   # ← ИЗМЕНЕНО

    m = await update.effective_chat.send_message("❎ Импорт отменён...")
    asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))
    context.user_data.pop("pending_import_all", None)

def register_upload_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("upload_words", cmd_upload_words))
    application.add_handler(MessageHandler(filters.Regex(r"^(Загрузить слова)$"), cmd_upload_words))
    application.add_handler(MessageHandler(filters.Regex(r"^(Добавить слова|Импортировать слова)$"), cmd_upload_words))
    application.add_handler(MessageHandler(filters.Document.ALL & (~filters.COMMAND), on_csv_document))
    application.add_handler(MessageHandler(filters.Regex(r"(?i)^(импортировать как есть)$"), on_confirm_import_all))
    application.add_handler(MessageHandler(filters.Regex(r"(?i)^(отменить импорт)$"), on_cancel_import))
