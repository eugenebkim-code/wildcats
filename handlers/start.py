"""Handles /start command and language selection."""

from telegram import Update
from telegram.ext import ContextTypes

from database import get_user_language, upsert_user
from google_logger import glogger
from keyboards import language_kb, main_menu_kb
from locales import t
from states import MAIN_MENU, SELECTING_LANGUAGE


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point — show language picker (or re-use saved language)."""
    user = update.effective_user
    saved_lang = get_user_language(user.id)  # type: ignore[arg-type]
    if saved_lang:
        context.user_data["language"] = saved_lang  # type: ignore[index]

    await glogger.log_action(user.id, user.username, "start", f"saved_lang={saved_lang or 'none'}")  # type: ignore[union-attr]

    await update.message.reply_text(  # type: ignore[union-attr]
        t("ru", "select_language"),   # always shown in all 3 languages
        reply_markup=language_kb(),
    )
    return SELECTING_LANGUAGE


async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Persist chosen language and show main menu."""
    query = update.callback_query
    await query.answer()

    lang_map = {"lang_ru": "ru", "lang_uz": "uz", "lang_en": "en"}
    lang = lang_map.get(query.data, "ru")  # type: ignore[arg-type]

    context.user_data["language"] = lang  # type: ignore[index]

    user = update.effective_user
    upsert_user(user.id, user.username, lang)  # type: ignore[union-attr]

    await glogger.log_action(user.id, user.username, "language_selected", lang)  # type: ignore[union-attr]

    await query.edit_message_text(
        t(lang, "welcome"),
        parse_mode="Markdown",
        reply_markup=main_menu_kb(lang),
    )
    return MAIN_MENU
