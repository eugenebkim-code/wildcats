import json
import os
import tempfile

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "wildcat_bot.db")

# Google integration (optional — logging is skipped if not configured)
# On Railway: set GOOGLE_CREDENTIALS_JSON to the full JSON content of the service account key.
# Locally: set GOOGLE_CREDENTIALS_PATH to the path of the JSON file.
GOOGLE_SPREADSHEET_ID: str = os.getenv("GOOGLE_SPREADSHEET_ID", "")

_creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
if _creds_json:
    # Write inline JSON to a temp file so gspread can load it normally
    _tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    _tmp.write(_creds_json)
    _tmp.close()
    GOOGLE_CREDENTIALS_PATH: str = _tmp.name
else:
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "assets/service_account.json")
