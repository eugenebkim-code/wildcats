"""Entry point — wire up all handlers and start polling."""

import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, GOOGLE_CREDENTIALS_PATH, GOOGLE_SPREADSHEET_ID
from database import init_db
from google_logger import glogger
from handlers.admin import (
    admin_callback,
    admin_command,
    doubt_command,
    export_command,
    history_callback,
    history_command,
    list_command,
    obs_command,
    verify_command,
)
from handlers.observation import (
    confirm_edit,
    confirm_send,
    handle_edit_field,
    location_method,
    photos_done,
    photos_skip,
    receive_coords_text,
    receive_date,
    receive_geo,
    receive_location_name,
    receive_notes,
    receive_observer,
    receive_photo,
    select_obs_type,
    select_species,
    start_observation,
)
from handlers.start import select_language, start_command
from states import (
    AWAITING_LOCATION,
    CONFIRMATION,
    EDITING_FIELD,
    ENTERING_DATE,
    ENTERING_LOCATION_NAME,
    ENTERING_NOTES,
    ENTERING_OBSERVER_NAME,
    MAIN_MENU,
    SELECTING_LANGUAGE,
    SELECTING_LOCATION_METHOD,
    SELECTING_OBS_TYPE,
    SELECTING_SPECIES,
    UPLOADING_PHOTOS,
)

logging.basicConfig(
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)


def build_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            SELECTING_LANGUAGE: [
                CallbackQueryHandler(select_language, pattern=r"^lang_"),
            ],
            MAIN_MENU: [
                CallbackQueryHandler(start_observation, pattern=r"^add_observation$"),
            ],
            SELECTING_SPECIES: [
                CallbackQueryHandler(select_species, pattern=r"^species_"),
            ],
            SELECTING_OBS_TYPE: [
                CallbackQueryHandler(select_obs_type, pattern=r"^obs_type_"),
            ],
            UPLOADING_PHOTOS: [
                MessageHandler(filters.PHOTO, receive_photo),
                CallbackQueryHandler(photos_done, pattern=r"^photos_done$"),
                CallbackQueryHandler(photos_skip, pattern=r"^photos_skip$"),
            ],
            ENTERING_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date),
            ],
            SELECTING_LOCATION_METHOD: [
                CallbackQueryHandler(location_method, pattern=r"^loc_"),
            ],
            AWAITING_LOCATION: [
                # Telegram location pin / GPS share
                MessageHandler(filters.LOCATION, receive_geo),
                # Manual "lat, lon" text
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_coords_text),
            ],
            ENTERING_LOCATION_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_location_name),
                CallbackQueryHandler(receive_location_name, pattern=r"^skip$"),
            ],
            ENTERING_OBSERVER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_observer),
                CallbackQueryHandler(receive_observer, pattern=r"^anonymous$"),
            ],
            ENTERING_NOTES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_notes),
                CallbackQueryHandler(receive_notes, pattern=r"^skip$"),
            ],
            CONFIRMATION: [
                CallbackQueryHandler(confirm_send, pattern=r"^confirm_send$"),
                CallbackQueryHandler(confirm_edit, pattern=r"^confirm_edit$"),
            ],
            EDITING_FIELD: [
                CallbackQueryHandler(
                    handle_edit_field,
                    pattern=r"^(edit_|back_to_confirmation)",
                ),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        allow_reentry=True,
        name="observation_conv",
        persistent=False,
    )


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Copy .env.example → .env and fill it in.")

    init_db()

    # Google logging — silently skipped if credentials/spreadsheet not configured
    if GOOGLE_SPREADSHEET_ID:
        glogger.init(
            credentials_path=GOOGLE_CREDENTIALS_PATH,
            spreadsheet_id=GOOGLE_SPREADSHEET_ID,
        )

    app = Application.builder().token(BOT_TOKEN).build()

    # ── admin commands (outside conversation, higher priority) ──────────────
    app.add_handler(CommandHandler("admin",   admin_command),  group=0)
    app.add_handler(CommandHandler("list",    list_command),   group=0)
    app.add_handler(CommandHandler("obs",     obs_command),    group=0)
    app.add_handler(CommandHandler("verify",  verify_command), group=0)
    app.add_handler(CommandHandler("doubt",   doubt_command),  group=0)
    app.add_handler(CommandHandler("export",  export_command),  group=0)
    app.add_handler(CommandHandler("history", history_command), group=0)
    # Admin inline buttons (verify/doubt from /obs message)
    app.add_handler(CallbackQueryHandler(admin_callback,    pattern=r"^adm_"),  group=0)
    app.add_handler(CallbackQueryHandler(history_callback,  pattern=r"^hist:"), group=0)

    # ── main conversation ────────────────────────────────────────────────────
    app.add_handler(build_conversation(), group=1)

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
