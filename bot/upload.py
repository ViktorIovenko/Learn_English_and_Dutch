# bot/upload.py
# Импорт слов из CSV + кнопки подтверждения
# [ИЗМЕНЕНО v4.7] После любых действий показываем постоянную клавиатуру «Учить слова / Добавить слова».

import os
import tempfile
from typing import List, Dict

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config import Config
from bot.db import is_user_registered, bulk_upsert_words
from bot.validators import (
    HELP_TEXT, parse_csv_to_rows, validate_example_usage, expected_word_for,
)
# [ДОБАВЛЕНО v4.7] клавиатура из auth
from bot.auth import get_persistent_keyboard

# ---------------- ХЕНДЛЕРЫ ----------------

async def cmd_upload_words(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    kb = get_persistent_keyboard(user.id)
    if not is_user_registered(Config.DB_PATH, user.id):
        await update.message.reply_text(
            "Сначала пройдите регистрацию: отправьте /start и введите пароль.",
            reply_markup=kb
        )
        return
    await update.message.reply_text("Загрузите .csv файл со словами.\n\n" + HELP_TEXT, reply_markup=kb)

async def on_csv_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    kb = get_persistent_keyboard(user.id)

    if not is_user_registered(Config.DB_PATH, user.id):
        await update.message.reply_text("Сначала пройдите регистрацию: отправьте /start и введите пароль.",
                                        reply_markup=kb)
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
        _, bad_rows = validate_example_usage(all_rows)

        if bad_rows:
            context.user_data["pending_import_all"] = all_rows
            lines = []
            for b in bad_rows[:30]:
                parts = []
                for fld in b["missing"]:
                    expected = expected_word_for(fld, b)
                    parts.append(f"{fld}: «{expected}»")
                lines.append(f"{b['number']}: " + "; ".join(parts))
            more = ""
            if len(bad_rows) > 30:
                more = f"\n... и ещё {len(bad_rows) - 30} строк(и)."
            kb_confirm = ReplyKeyboardMarkup(
                [["Импортировать как есть", "Отменить импорт"]],
                resize_keyboard=True
            )
            await update.message.reply_text(
                "⚠ Обнаружены строки, где слово не встречается в примере.\n"
                "Формат: №: ex_*: «ожидаемый вариант(ы)»\n\n"
                + "\n".join(lines) + more +
                "\n\nВыберите действие:",
                reply_markup=kb_confirm
            )
            return

        count = bulk_upsert_words(Config.DB_PATH, all_rows)
        await update.message.reply_text(
            f"✅ Импортировано записей: {count}\n"
            f"Например: {all_rows[0]['number']} — {all_rows[0]['nl']} / {all_rows[0]['en']} / {all_rows[0]['ru']}",
            reply_markup=kb
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка импорта: {e}\n\n" + HELP_TEXT, reply_markup=kb)

# Подтверждение: импортировать ПОЛНЫЙ файл, несмотря на ошибки
async def on_confirm_import_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    rows: List[Dict[str, str]] = context.user_data.get("pending_import_all") or []
    kb = get_persistent_keyboard(user.id)

    if not rows:
        await update.message.reply_text("Нет данных к импорту. Пришлите CSV снова.",
                                        reply_markup=kb)
        return
    count = bulk_upsert_words(Config.DB_PATH, rows)
    context.user_data.pop("pending_import_all", None)
    await update.message.reply_text(
        f"✅ Импортировано записей (весь файл): {count}.",
        reply_markup=kb
    )

# Отмена импорта
async def on_cancel_import(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    context.user_data.pop("pending_import_all", None)
    await update.message.reply_text("Импорт отменён. Готово к работе.",
                                    reply_markup=get_persistent_keyboard(user.id))

def register_upload_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("upload_words", cmd_upload_words))
    application.add_handler(MessageHandler(filters.Regex(r"^(Загрузить слова)$"), cmd_upload_words))
    application.add_handler(MessageHandler(filters.Regex(r"^(Добавить слова)$"), cmd_upload_words))
    application.add_handler(MessageHandler(filters.Document.ALL & (~filters.COMMAND), on_csv_document))
    application.add_handler(MessageHandler(filters.Regex(r"^(Импортировать как есть)$"), on_confirm_import_all))
    application.add_handler(MessageHandler(filters.Regex(r"^(Отменить импорт)$"), on_cancel_import))
