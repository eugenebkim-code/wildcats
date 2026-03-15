import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "wildcat_bot.db")

# Google integration (optional — logging is skipped if not configured)
GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_SPREADSHEET_ID: str   = os.getenv("GOOGLE_SPREADSHEET_ID", "")
