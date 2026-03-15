"""
Google Sheets logging + local photo storage.

Two sheets inside one Spreadsheet:
  • "Observations" — one row per submitted observation (with local photo filenames)
  • "Activity"     — one row per user action at every conversation step

Photos are downloaded from Telegram and saved to a local PHOTOS_DIR folder.
The filenames are stored in the Observations sheet.

Initialise once at startup via  glogger.init(...)  — if credentials are
missing the module degrades gracefully (all calls become no-ops).
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)

# ── lazy imports (only needed when Google is configured) ─────────────────────
_gspread = None
_Credentials = None


def _lazy_import() -> bool:
    global _gspread, _Credentials
    try:
        import gspread as _gs
        from google.oauth2.service_account import Credentials as _C
        _gspread, _Credentials = _gs, _C
        return True
    except ImportError as exc:
        log.warning("Google logging libraries not installed: %s", exc)
        return False


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

_OBS_HEADERS = [
    "observation_id", "submitted_at", "telegram_id", "username",
    "language", "species", "observation_type", "date",
    "latitude", "longitude", "location_name", "observer_name",
    "notes", "photos", "status",
]

_ACTIVITY_HEADERS = [
    "timestamp", "telegram_id", "username", "action", "details",
]


class GoogleLogger:
    def __init__(self) -> None:
        self._ready = False
        self._obs_ws = None
        self._activity_ws = None

    # ── initialisation ────────────────────────────────────────────────────────

    def init(self, credentials_path: str, spreadsheet_id: str) -> None:
        if not _lazy_import():
            return
        try:
            creds = _Credentials.from_service_account_file(  # type: ignore[union-attr]
                credentials_path, scopes=_SCOPES
            )
            gc = _gspread.authorize(creds)  # type: ignore[union-attr]
            spreadsheet = gc.open_by_key(spreadsheet_id)

            self._obs_ws      = self._ensure_sheet(spreadsheet, "Observations", _OBS_HEADERS)
            self._activity_ws = self._ensure_sheet(spreadsheet, "Activity",     _ACTIVITY_HEADERS)
            self._ready = True
            log.info("Google Sheets logger initialised (spreadsheet=%s)", spreadsheet_id)
        except Exception as exc:
            log.warning("Google logging disabled — init failed: %s", exc)

    @staticmethod
    def _ensure_sheet(spreadsheet, name: str, headers: list[str]):
        try:
            ws = spreadsheet.worksheet(name)
        except _gspread.WorksheetNotFound:  # type: ignore[union-attr]
            ws = spreadsheet.add_worksheet(name, rows=5000, cols=len(headers))
            ws.append_row(headers, value_input_option="RAW")
        return ws

    # ── public async API ──────────────────────────────────────────────────────

    async def log_action(
        self,
        telegram_id: int,
        username: str | None,
        action: str,
        details: str = "",
    ) -> None:
        if not self._ready:
            return
        row = [_now(), str(telegram_id), username or "", action, details]
        await _run(self._activity_ws.append_row, row, value_input_option="RAW")

    async def log_observation(
        self,
        bot: Any,
        obs_data: dict,
        obs_id: int,
        username: str | None,
    ) -> None:
        if not self._ready:
            return

        # Store Telegram file_ids as a comma-separated string
        file_ids = obs_data.get("photos", [])
        photos_str = ", ".join(file_ids) if file_ids else ""

        from locales import obs_type_name, species_name
        row = [
            str(obs_id),
            _now(),
            str(obs_data.get("telegram_id", "")),
            username or "",
            obs_data.get("language", ""),
            species_name(obs_data.get("species", ""), "ru"),
            obs_type_name(obs_data.get("observation_type", ""), "ru"),
            obs_data.get("date", ""),
            obs_data.get("latitude", ""),
            obs_data.get("longitude", ""),
            obs_data.get("location_name", ""),
            obs_data.get("observer_name", ""),
            obs_data.get("notes", ""),
            photos_str,
            "pending",
        ]
        await _run(self._obs_ws.append_row, row, value_input_option="RAW")


# ── utilities ─────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


async def _run(fn, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# ── singleton ─────────────────────────────────────────────────────────────────

glogger = GoogleLogger()
