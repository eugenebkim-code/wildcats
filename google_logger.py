"""
Google Sheets + Google Drive logging.

Two sheets inside one Spreadsheet:
  • "Observations" — one row per submitted observation (with Drive photo links)
  • "Activity"     — one row per user action at every conversation step

Photos are downloaded from Telegram and uploaded to a Google Drive folder;
shareable view links are stored in the Observations sheet.

Initialise once at startup via  glogger.init(...)  — if credentials are
missing the module degrades gracefully (all calls become no-ops).
"""

import asyncio
import io
import logging
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)

# ── lazy imports (only needed when Google is configured) ─────────────────────
_gspread = None
_Credentials = None
_build = None
_MediaUpload = None


def _lazy_import() -> bool:
    global _gspread, _Credentials, _build, _MediaUpload
    try:
        import gspread as _gs
        from google.oauth2.service_account import Credentials as _C
        from googleapiclient.discovery import build as _b
        from googleapiclient.http import MediaIoBaseUpload as _M
        _gspread, _Credentials, _build, _MediaUpload = _gs, _C, _b, _M
        return True
    except ImportError as exc:
        log.warning("Google logging libraries not installed: %s", exc)
        return False


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
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
        self._obs_ws = None       # gspread Worksheet
        self._activity_ws = None  # gspread Worksheet
        self._drive = None        # Drive v3 service
        self._folder_id: str | None = None

    # ── initialisation ────────────────────────────────────────────────────────

    def init(
        self,
        credentials_path: str,
        spreadsheet_id: str,
        drive_folder_id: str | None = None,
    ) -> None:
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
            self._drive       = _build("drive", "v3", credentials=creds)  # type: ignore[union-attr]
            self._folder_id   = drive_folder_id
            self._ready       = True
            log.info("Google Sheets logger initialised (spreadsheet=%s)", spreadsheet_id)
        except Exception as exc:
            log.warning("Google logging disabled — init failed: %s", exc)

    @staticmethod
    def _ensure_sheet(spreadsheet, name: str, headers: list[str]):
        """Return existing worksheet or create it with a header row."""
        try:
            ws = spreadsheet.worksheet(name)
        except _gspread.WorksheetNotFound:  # type: ignore[union-attr]
            ws = spreadsheet.add_worksheet(name, rows=5000, cols=len(headers))
            ws.append_row(headers, value_input_option="RAW")
        return ws

    # ── public async API ─────────────────────────────────────────────────────

    async def log_action(
        self,
        telegram_id: int,
        username: str | None,
        action: str,
        details: str = "",
    ) -> None:
        """Log a single user action to the Activity sheet (non-blocking)."""
        if not self._ready:
            return
        row = [
            _now(),
            str(telegram_id),
            username or "",
            action,
            details,
        ]
        await _run(self._activity_ws.append_row, row, value_input_option="RAW")

    async def log_observation(
        self,
        bot: Any,
        obs_data: dict,
        obs_id: int,
        username: str | None,
    ) -> None:
        """
        Upload photos to Drive, then append a row to the Observations sheet.
        obs_data  — the dict from context.user_data["obs"]
        obs_id    — the integer ID returned by save_observation()
        """
        if not self._ready:
            return

        photo_links = await self._upload_photos(bot, obs_data.get("photos", []), obs_id)

        from locales import obs_type_name, species_name  # local import avoids circular
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
            "\n".join(photo_links),
            "pending",
        ]
        await _run(self._obs_ws.append_row, row, value_input_option="RAW")

    # ── photo upload ─────────────────────────────────────────────────────────

    async def _upload_photos(self, bot: Any, file_ids: list[str], obs_id: int) -> list[str]:
        links: list[str] = []
        for i, file_id in enumerate(file_ids, 1):
            try:
                tg_file = await bot.get_file(file_id)
                buf = io.BytesIO()
                await tg_file.download_to_memory(buf)
                photo_bytes = buf.getvalue()

                # Guess extension from Telegram file path
                ext = "jpg"
                if tg_file.file_path:
                    ext = tg_file.file_path.rsplit(".", 1)[-1] or "jpg"

                filename = f"obs_{obs_id}_photo_{i}.{ext}"
                link = await _run(self._upload_to_drive, photo_bytes, filename, ext)
                links.append(link)
                log.info("Uploaded photo %s → %s", filename, link)
            except Exception as exc:
                log.warning("Photo upload failed (file_id=%s): %s", file_id, exc)
                links.append(f"[upload error: {exc}]")
        return links

    def _upload_to_drive(self, data: bytes, filename: str, ext: str) -> str:
        """Synchronous Drive upload — run via asyncio.to_thread."""
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "gif": "image/gif",
                    "webp": "image/webp"}
        mime = mime_map.get(ext.lower(), "application/octet-stream")

        meta: dict = {"name": filename}
        if self._folder_id:
            meta["parents"] = [self._folder_id]

        media = _MediaUpload(io.BytesIO(data), mimetype=mime, resumable=False)  # type: ignore[call-arg]
        file = (
            self._drive.files()
            .create(body=meta, media_body=media, fields="id")
            .execute()
        )
        file_id = file["id"]

        # Make publicly viewable (read-only)
        self._drive.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()

        return f"https://drive.google.com/file/d/{file_id}/view"


# ── utilities ─────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


async def _run(fn, *args, **kwargs):
    """Run a blocking function in a thread executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# ── singleton ─────────────────────────────────────────────────────────────────

glogger = GoogleLogger()
