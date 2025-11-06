# bot/upload.py
# Импорт слов из CSV + кнопки подтверждения
# [ИЗМЕНЕНО v4.19] Клавиатура подтверждения тоже persistent + небольшая пауза после Remove().
# [ИЗМЕНЕНО v4.18] Сразу после загрузки CSV показываем кнопки «Импортировать как есть / Отменить импорт».
# [ИЗМЕНЕНО v4.14] Перед показом постоянного меню убираем клавиатуру подтверждения ReplyKeyboardRemove().
# [ИЗМЕНЕНО v4.12] После «Импортировать как есть» мгновенно возвращаем меню ("⏳ Импортирую...").
# [ИЗМЕНЕНО v4.13] После «Отменить импорт» мгновенно возвращаем меню ("❎ Импорт отменён...").
# [ИЗМЕНЕНО v4.15] Всегда предлагаем кнопки, если есть строки к импорту (даже без ошибок).

import os
import tempfile
import sqlite3
import asyncio  # [ДОБАВЛЕНО v4.19]
from typing import List, Dict

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config import Config
from bot.db import is_user_registered, bulk_upsert_words
from bot.validators import (
    HELP_TEXT, parse_csv_to_rows, validate_example_usage, expected_word_for,
)
from bot.auth import get_persistent_keyboard

# ---------------- УТИЛИТЫ ----------------
def _norm_nl(nl: str) -> str:
    return (nl or "").strip().lower()

def _get_existing_nl_set(db_path: str) -> set[str]:
    existing = set()
    try:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT nl FROM words")
            for (nl,) in cur.fetchall():
                existing.add(_norm_nl(nl))
        finally:
            conn.close()
    except Exception:
        pass
    return existing

def _format_full_list(items: List[tuple], header_emoji: str, header_text: str) -> str:
    if not items:
        return ""
    lines = [f"{header_emoji} {header_text}: {len(items)}"]
    for n, w in items:
        n = n if n is not None else "?"
        w = w if w is not None else ""
        lines.append(f" - {n} ({w})")
    return "\n".join(lines)

async def _send_long(update: Update, text: str, kb, chunk_limit: int = 3500) -> None:
    if len(text) <= chunk_limit:
        await update.message.reply_text(text, reply_markup=kb)
        return
    parts, acc, acc_len = [], [], 0
    for line in text.splitlines():
        ln = len(line) + 1
        if acc_len + ln > chunk_limit and acc:
            parts.append("\n".join(acc))
            acc, acc_len = [line], ln
        else:
            acc.append(line); acc_len += ln
    if acc:
        parts.append("\n".join(acc))
    for i, p in enumerate(parts):
        await update.message.reply_text(p, reply_markup=kb if i == 0 else None)

def _filter_duplicates_by_nl(rows: List[Dict[str, str]], db_path: str):
    existing_db = _get_existing_nl_set(db_path)
    seen_in_file = set()
    filtered = []
    skipped_in_file = []
    skipped_in_db = []
    for r in rows:
        nl = _norm_nl(r.get("nl", ""))
        if not nl:
            filtered.append(r)
            continue
        if nl in seen_in_file:
            skipped_in_file.append((r.get("number", "?"), r.get("nl", "")))
            continue
        if nl in existing_db:
            skipped_in_db.append((r.get("number", "?"), r.get("nl", "")))
            continue
        seen_in_file.add(nl)
        filtered.append(r)
    return filtered, skipped_in_file, skipped_in_db

# ---------------- ХЕНДЛЕРЫ ----------------
async def cmd_upload_words(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Если pending_import_all есть — сразу предлагаем подтвердить; иначе просим прислать CSV."""
    user = update.effective_user
    kb = get_persistent_keyboard(user.id)

    if not is_user_registered(Config.DB_PATH, user.id):
        await update.message.reply_text(
            "Сначала пройдите регистрацию: отправьте /start и введите пароль.",
            reply_markup=kb
        )
        return

    pending = context.user_data.get("pending_import_all") or []
    if pending:
        # [ИЗМЕНЕНО v4.19] Удаляем старую клавиатуру и даём клиенту «переключиться»
        await update.message.reply_text("…", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(0.2)

        kb_confirm = ReplyKeyboardMarkup(
            [["Импортировать как есть", "Отменить импорт"]],
            resize_keyboard=True,
            is_persistent=True,          # ← было не persistent, из-за чего иногда не показывалось
            one_time_keyboard=False
        )
        await update.message.reply_text(
            f"Подготовлено к импорту строк: {len(pending)}.\nИмпортировать сейчас?",
            reply_markup=kb_confirm
        )
        return

    await update.message.reply_text("Загрузите .csv файл со словами.\n\n" + HELP_TEXT, reply_markup=kb)

async def on_csv_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    kb = get_persistent_keyboard(user.id)

    if not is_user_registered(Config.DB_PATH, user.id):
        await update.message.reply_text(
            "Сначала пройдите регистрацию: отправьте /start и введите пароль.",
            reply_markup=kb
        )
        return

    doc = update.message.document
    if not doc:
        return

    fname = (doc.file_name or "").lower()
    if not (fname.endswith(".csv") or (doc.mime_type and "csv" in doc.mime_type.lower())):
        await update.message.reply_text("Это не .csv файл. Пожалуйста, пришлите CSV.", reply_markup=kb)
        return

    tmpdir = tempfile.mkdtemp(prefix="csv_upload_")
    tmp_path = os.path.join(tmpdir, fname or "words.csv")
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(custom_path=tmp_path)

    try:
        all_rows: List[Dict[str, str]] = parse_csv_to_rows(tmp_path)

        # 1) Фильтр дублей по NL
        filtered_rows, skipped_in_file, skipped_in_db = _filter_duplicates_by_nl(all_rows, Config.DB_PATH)

        if not filtered_rows:
            blocks = ["⚠ Все загруженные слова уже есть (или повторяются в самом файле) и были пропущены."]
            if skipped_in_file:
                blocks.append(_format_full_list(skipped_in_file, "🔁", "Повторы внутри файла"))
            if skipped_in_db:
                blocks.append(_format_full_list(skipped_in_db, "📚", "Уже были в базе"))
            await _send_long(update, "\n\n".join(blocks), kb)
            return

        # 2) Валидация примеров
        _, bad_rows = validate_example_usage(filtered_rows)

        # 3) Сохраняем pending для подтверждения
        context.user_data["pending_import_all"] = filtered_rows

        # 4) Текст отчёта
        extra_blocks = []
        if skipped_in_file:
            extra_blocks.append(_format_full_list(skipped_in_file, "🔁", "Пропущены повторы внутри файла"))
        if skipped_in_db:
            extra_blocks.append(_format_full_list(skipped_in_db, "📚", "Пропущены как уже существующие в базе"))

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

        # 5) Показ клавиатуры подтверждения
        await update.message.reply_text("…", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(0.2)  # [ДОБАВЛЕНО v4.19] маленькая пауза для десктоп-клиента

        kb_confirm = ReplyKeyboardMarkup(
            [["Импортировать как есть", "Отменить импорт"]],
            resize_keyboard=True,
            is_persistent=True,          # [ДОБАВЛЕНО v4.19]
            one_time_keyboard=False
        )
        await _send_long(update, msg + "\n\nВыберите действие:", kb_confirm)
        return

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка импорта: {e}\n\n" + HELP_TEXT, reply_markup=kb)

# Подтверждение: импортировать ПОЛНЫЙ файл (после фильтра дублей)
async def on_confirm_import_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    rows: List[Dict[str, str]] = context.user_data.get("pending_import_all") or []
    kb = get_persistent_keyboard(user.id)

    if not rows:
        await update.message.reply_text("Нет данных к импорту. Пришлите CSV снова.", reply_markup=kb)
        return

    # 1) Убираем confirm-клавиатуру и мгновенно возвращаем постоянное меню
    await update.message.reply_text("…", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("⏳ Импортирую...", reply_markup=kb)

    # 2) Повторная фильтрация на случай гонок
    filtered_rows, skipped_in_file, skipped_in_db = _filter_duplicates_by_nl(rows, Config.DB_PATH)

    if not filtered_rows:
        blocks = ["⚠ Все загруженные слова уже есть (или повторяются в самом файле) и были пропущены."]
        if skipped_in_file:
            blocks.append(_format_full_list(skipped_in_file, "🔁", "Внутри файла повторов"))
        if skipped_in_db:
            blocks.append(_format_full_list(skipped_in_db, "📚", "Уже были в базе"))
        await _send_long(update, "\n\n".join(blocks), kb)
        context.user_data.pop("pending_import_all", None)
        return

    # 3) Импорт
    count = bulk_upsert_words(Config.DB_PATH, filtered_rows)
    context.user_data.pop("pending_import_all", None)

    blocks = [f"✅ Импортировано записей (после фильтра дублей): {count}"]
    if skipped_in_file:
        blocks.append(_format_full_list(skipped_in_file, "🔁", "Пропущены повторы внутри файла"))
    if skipped_in_db:
        blocks.append(_format_full_list(skipped_in_db, "📚", "Пропущены как уже существующие в базе"))

    await _send_long(update, "\n\n".join(blocks), kb)

# Отмена импорта
async def on_cancel_import(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    kb = get_persistent_keyboard(user.id)

    await update.message.reply_text("…", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("❎ Импорт отменён...", reply_markup=kb)
    context.user_data.pop("pending_import_all", None)
    await update.message.reply_text("Импорт отменён. Готово к работе.", reply_markup=kb)

def register_upload_handlers(application: Application) -> None:
    # Группа 0 — раньше общего on_text (который в группе 100)
    application.add_handler(CommandHandler("upload_words", cmd_upload_words))
    application.add_handler(MessageHandler(filters.Regex(r"^(Загрузить слова)$"), cmd_upload_words))
    application.add_handler(MessageHandler(filters.Regex(r"^(Добавить слова)$"), cmd_upload_words))

    # Документы (CSV)
    application.add_handler(MessageHandler(filters.Document.ALL & (~filters.COMMAND), on_csv_document))

    # Подтверждение/отмена
    application.add_handler(MessageHandler(filters.Regex(r"^(Импортировать как есть)$"), on_confirm_import_all))
    application.add_handler(MessageHandler(filters.Regex(r"^(Отменить импорт)$"), on_cancel_import))
