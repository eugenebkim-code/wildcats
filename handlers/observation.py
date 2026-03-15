"""
All handlers for the 8-step observation conversation.

State flow (normal path):
  MAIN_MENU
    → start_observation
  SELECTING_SPECIES
    → select_species
  SELECTING_OBS_TYPE
    → select_obs_type
  UPLOADING_PHOTOS
    → receive_photo / photos_done / photos_skip
  ENTERING_DATE
    → receive_date
  SELECTING_LOCATION_METHOD
    → location_method
  AWAITING_LOCATION
    → receive_geo  (Telegram location message)
    → receive_coords_text  (manual "lat, lon" text)
  ENTERING_LOCATION_NAME
    → receive_location_name / skip
  ENTERING_OBSERVER_NAME
    → receive_observer / anonymous
  ENTERING_NOTES
    → receive_notes / skip
  CONFIRMATION
    → confirm_send / confirm_edit
  EDITING_FIELD
    → handle_edit_field  (routes back into the appropriate step)

Edit mode:
  context.user_data["editing_field"] is set when the user wants to change
  a specific field.  Each step-completing handler checks this flag:
  if set → clear it and jump straight back to CONFIRMATION.
"""

import re
from datetime import datetime

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

import assets as _assets

from config import ADMIN_IDS
from google_logger import glogger
from database import save_observation
from keyboards import (
    anonymous_kb,
    confirmation_kb,
    edit_field_kb,
    geo_request_kb,
    location_method_kb,
    main_menu_kb,
    obs_type_kb,
    photos_kb,
    skip_kb,
    species_kb,
)
from locales import obs_type_name, species_name, t
from states import (
    AWAITING_LOCATION,
    CONFIRMATION,
    EDITING_FIELD,
    ENTERING_DATE,
    ENTERING_LOCATION_NAME,
    ENTERING_NOTES,
    ENTERING_OBSERVER_NAME,
    MAIN_MENU,
    SELECTING_LOCATION_METHOD,
    SELECTING_OBS_TYPE,
    SELECTING_SPECIES,
    UPLOADING_PHOTOS,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("language", "ru")  # type: ignore[return-value]


def _obs(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data["obs"]  # type: ignore[index]


def _is_editing(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(context.user_data.get("editing_field"))  # type: ignore[union-attr]


async def _log(update: Update, action: str, details: str = "") -> None:
    u = update.effective_user
    await glogger.log_action(u.id, u.username, action, details)  # type: ignore[union-attr]


def _build_summary(data: dict, lang: str) -> str:
    """Build the confirmation/summary text."""
    lines = [t(lang, "confirmation_title"), ""]

    lines.append(t(lang, "confirmation_species", value=species_name(data.get("species", ""), lang)))
    lines.append(t(lang, "confirmation_obs_type", value=obs_type_name(data.get("observation_type", ""), lang)))
    lines.append(t(lang, "confirmation_date", value=data.get("date", "—")))

    if data.get("latitude") is not None:
        lines.append(t(lang, "confirmation_coords", lat=data["latitude"], lon=data["longitude"]))
    else:
        lines.append(t(lang, "confirmation_no_coords"))

    if data.get("location_name"):
        lines.append(t(lang, "confirmation_location_name", value=data["location_name"]))
    else:
        lines.append(t(lang, "confirmation_no_location_name"))

    lines.append(t(lang, "confirmation_observer", value=data.get("observer_name", "—")))

    photos = data.get("photos", [])
    if photos:
        lines.append(t(lang, "confirmation_photos", count=len(photos)))
    else:
        lines.append(t(lang, "confirmation_no_photos"))

    if data.get("notes"):
        lines.append(t(lang, "confirmation_notes", value=data["notes"]))
    else:
        lines.append(t(lang, "confirmation_no_notes"))

    return "\n".join(lines)


async def _send_species_gallery(chat_id: int, context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    """Send each species as its own photo with a select button underneath."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    for key in _assets.SPECIES_PHOTOS:
        data = _assets.photo_bytes(key)
        if not data:
            continue
        name = species_name(key, lang)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"✓  {name}", callback_data=f"species_{key}")]])
        await context.bot.send_photo(chat_id=chat_id, photo=data, caption=name, reply_markup=kb)

    # "Not sure" has no photo — send as a standalone button
    unsure = species_name("unsure", lang)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(unsure, callback_data="species_unsure")]])
    await context.bot.send_message(chat_id=chat_id, text=unsure, reply_markup=kb)


async def _show_confirmation(send_fn, lang: str, data: dict) -> int:
    """Send or edit a message showing the observation summary."""
    await send_fn(
        _build_summary(data, lang),
        parse_mode="Markdown",
        reply_markup=confirmation_kb(lang),
    )
    return CONFIRMATION


# ── step 0: entry point ──────────────────────────────────────────────────────

async def start_observation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    await _log(update, "observation_started")

    context.user_data["obs"] = {  # type: ignore[index]
        "photos": [],
        "telegram_id": update.effective_user.id,  # type: ignore[union-attr]
        "language": lang,
    }

    # Acknowledge button tap
    await query.edit_message_text(t(lang, "step_species"), parse_mode="Markdown")

    # Send each species as individual photo + select button
    await _send_species_gallery(query.message.chat_id, context, lang)  # type: ignore[union-attr]
    return SELECTING_SPECIES


# ── step 1: species ──────────────────────────────────────────────────────────

async def select_species(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    _obs(context)["species"] = query.data.removeprefix("species_")  # type: ignore[union-attr]
    await _log(update, "species_selected", _obs(context)["species"])

    # Button is on a photo message — remove the keyboard to mark it as selected,
    # then reply with the next step as a new message (can't edit_message_text on photos)
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    if _is_editing(context):
        context.user_data.pop("editing_field")  # type: ignore[union-attr]
        return await _show_confirmation(query.message.reply_text, lang, _obs(context))  # type: ignore[union-attr]

    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "step_obs_type"),
        parse_mode="Markdown",
        reply_markup=obs_type_kb(lang),
    )
    return SELECTING_OBS_TYPE


# ── step 2: observation type ──────────────────────────────────────────────────

async def select_obs_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    _obs(context)["observation_type"] = query.data.removeprefix("obs_type_")  # type: ignore[union-attr]
    await _log(update, "obs_type_selected", _obs(context)["observation_type"])

    if _is_editing(context):
        context.user_data.pop("editing_field")  # type: ignore[union-attr]
        return await _show_confirmation(query.edit_message_text, lang, _obs(context))

    await query.edit_message_text(
        t(lang, "step_photos"),
        parse_mode="Markdown",
        reply_markup=photos_kb(lang),
    )
    return UPLOADING_PHOTOS


# ── step 3: photos ───────────────────────────────────────────────────────────

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    file_id = update.message.photo[-1].file_id  # type: ignore[index]
    _obs(context)["photos"].append(file_id)
    count = len(_obs(context)["photos"])
    await _log(update, "photo_added", f"count={count} file_id={file_id}")

    await update.message.reply_text(  # type: ignore[union-attr]
        t(lang, "photo_added", count=count),
        reply_markup=photos_kb(lang),
    )
    return UPLOADING_PHOTOS


async def photos_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    await _log(update, "photos_finalized", f"total={len(_obs(context)['photos'])}")

    if _is_editing(context):
        context.user_data.pop("editing_field")  # type: ignore[union-attr]
        return await _show_confirmation(query.edit_message_text, lang, _obs(context))

    await query.edit_message_text(
        t(lang, "step_date"),
        parse_mode="Markdown",
    )
    return ENTERING_DATE


async def photos_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    _obs(context)["photos"] = []
    await _log(update, "photos_skipped")

    if _is_editing(context):
        context.user_data.pop("editing_field")  # type: ignore[union-attr]
        return await _show_confirmation(query.edit_message_text, lang, _obs(context))

    await query.edit_message_text(
        t(lang, "step_date"),
        parse_mode="Markdown",
    )
    return ENTERING_DATE


# ── step 4: date ─────────────────────────────────────────────────────────────

async def receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    text = update.message.text.strip()  # type: ignore[union-attr]

    try:
        parsed = datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text(  # type: ignore[union-attr]
            t(lang, "date_invalid"), parse_mode="Markdown"
        )
        return ENTERING_DATE

    if parsed > datetime.now():
        await update.message.reply_text(  # type: ignore[union-attr]
            t(lang, "date_future")
        )
        return ENTERING_DATE

    _obs(context)["date"] = text
    await _log(update, "date_entered", text)

    if _is_editing(context):
        context.user_data.pop("editing_field")  # type: ignore[union-attr]
        return await _show_confirmation(update.message.reply_text, lang, _obs(context))

    await update.message.reply_text(  # type: ignore[union-attr]
        t(lang, "step_location"),
        parse_mode="Markdown",
        reply_markup=location_method_kb(lang),
    )
    return SELECTING_LOCATION_METHOD


# ── step 5: location ─────────────────────────────────────────────────────────

async def location_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    method = query.data  # loc_current | loc_map | loc_manual

    await _log(update, "location_method_chosen", method)

    if method == "loc_manual":
        await query.edit_message_text(
            t(lang, "location_manual_hint"), parse_mode="Markdown"
        )
        return AWAITING_LOCATION  # text handler picks up the input

    # loc_current or loc_map → request Telegram geo
    hint_key = "location_current_hint" if method == "loc_current" else "location_map_hint"
    await query.edit_message_text(t(lang, hint_key), parse_mode="Markdown")
    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "awaiting_geo"),
        reply_markup=geo_request_kb(lang),
    )
    return AWAITING_LOCATION


async def receive_geo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle a Telegram location message (GPS or map pin)."""
    lang = _lang(context)
    loc = update.message.location  # type: ignore[union-attr]

    _obs(context)["latitude"]  = round(loc.latitude, 6)
    _obs(context)["longitude"] = round(loc.longitude, 6)

    await _log(update, "location_set_geo",
               f"{_obs(context)['latitude']}, {_obs(context)['longitude']}")

    await update.message.reply_text(  # type: ignore[union-attr]
        t(lang, "location_received", lat=_obs(context)["latitude"], lon=_obs(context)["longitude"]),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    if _is_editing(context):
        context.user_data.pop("editing_field")  # type: ignore[union-attr]
        return await _show_confirmation(update.message.reply_text, lang, _obs(context))

    await update.message.reply_text(  # type: ignore[union-attr]
        t(lang, "step_location_name"),
        parse_mode="Markdown",
        reply_markup=skip_kb(lang),
    )
    return ENTERING_LOCATION_NAME


async def receive_coords_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle manually typed 'lat, lon' coordinates."""
    lang = _lang(context)
    raw = update.message.text.strip()  # type: ignore[union-attr]

    match = re.fullmatch(r"(-?\d+\.?\d*)\s*[,;\s]\s*(-?\d+\.?\d*)", raw)
    if not match:
        await update.message.reply_text(  # type: ignore[union-attr]
            t(lang, "location_invalid"), parse_mode="Markdown"
        )
        return AWAITING_LOCATION

    lat, lon = float(match.group(1)), float(match.group(2))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        await update.message.reply_text(  # type: ignore[union-attr]
            t(lang, "location_out_of_range")
        )
        return AWAITING_LOCATION

    _obs(context)["latitude"]  = round(lat, 6)
    _obs(context)["longitude"] = round(lon, 6)

    await _log(update, "location_set_manual", f"{round(lat, 6)}, {round(lon, 6)}")

    await update.message.reply_text(  # type: ignore[union-attr]
        t(lang, "location_received", lat=round(lat, 6), lon=round(lon, 6)),
        parse_mode="Markdown",
    )

    if _is_editing(context):
        context.user_data.pop("editing_field")  # type: ignore[union-attr]
        return await _show_confirmation(update.message.reply_text, lang, _obs(context))

    await update.message.reply_text(  # type: ignore[union-attr]
        t(lang, "step_location_name"),
        parse_mode="Markdown",
        reply_markup=skip_kb(lang),
    )
    return ENTERING_LOCATION_NAME


# ── step 6: location name ────────────────────────────────────────────────────

async def receive_location_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)

    if update.callback_query:
        await update.callback_query.answer()
        _obs(context)["location_name"] = None
        await _log(update, "location_name_set", "skipped")

        if _is_editing(context):
            context.user_data.pop("editing_field")  # type: ignore[union-attr]
            return await _show_confirmation(
                update.callback_query.edit_message_text, lang, _obs(context)
            )

        await update.callback_query.edit_message_text(
            t(lang, "step_observer"),
            parse_mode="Markdown",
            reply_markup=anonymous_kb(lang),
        )
    else:
        _obs(context)["location_name"] = update.message.text.strip()  # type: ignore[union-attr]
        await _log(update, "location_name_set", _obs(context)["location_name"])

        if _is_editing(context):
            context.user_data.pop("editing_field")  # type: ignore[union-attr]
            return await _show_confirmation(update.message.reply_text, lang, _obs(context))  # type: ignore[union-attr]

        await update.message.reply_text(  # type: ignore[union-attr]
            t(lang, "step_observer"),
            parse_mode="Markdown",
            reply_markup=anonymous_kb(lang),
        )

    return ENTERING_OBSERVER_NAME


# ── step 7: observer name ────────────────────────────────────────────────────

async def receive_observer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)

    if update.callback_query:
        await update.callback_query.answer()
        _obs(context)["observer_name"] = t(lang, "anonymous").lstrip("🕵 ")
        await _log(update, "observer_set", "anonymous")

        if _is_editing(context):
            context.user_data.pop("editing_field")  # type: ignore[union-attr]
            return await _show_confirmation(
                update.callback_query.edit_message_text, lang, _obs(context)
            )

        await update.callback_query.edit_message_text(
            t(lang, "step_notes"),
            parse_mode="Markdown",
            reply_markup=skip_kb(lang),
        )
    else:
        _obs(context)["observer_name"] = update.message.text.strip()  # type: ignore[union-attr]
        await _log(update, "observer_set", _obs(context)["observer_name"])

        if _is_editing(context):
            context.user_data.pop("editing_field")  # type: ignore[union-attr]
            return await _show_confirmation(update.message.reply_text, lang, _obs(context))  # type: ignore[union-attr]

        await update.message.reply_text(  # type: ignore[union-attr]
            t(lang, "step_notes"),
            parse_mode="Markdown",
            reply_markup=skip_kb(lang),
        )

    return ENTERING_NOTES


# ── step 8: notes ────────────────────────────────────────────────────────────

async def receive_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)

    if update.callback_query:
        await update.callback_query.answer()
        _obs(context)["notes"] = None
        await _log(update, "notes_set", "skipped")
        return await _show_confirmation(
            update.callback_query.edit_message_text, lang, _obs(context)
        )
    else:
        _obs(context)["notes"] = update.message.text.strip()  # type: ignore[union-attr]
        await _log(update, "notes_set", _obs(context)["notes"][:120])
        return await _show_confirmation(update.message.reply_text, lang, _obs(context))  # type: ignore[union-attr]


# ── confirmation ─────────────────────────────────────────────────────────────

async def confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    obs_id = save_observation(_obs(context))
    user = update.effective_user  # type: ignore[union-attr]

    await _log(update, "observation_submitted", f"obs_id={obs_id}")

    # Log to Google Sheets + upload photos to Drive (non-blocking)
    await glogger.log_observation(
        context.bot,
        _obs(context),
        obs_id,
        user.username,
    )

    await query.edit_message_text(
        t(lang, "success", obs_id=obs_id),
        parse_mode="Markdown",
        reply_markup=main_menu_kb(lang),
    )

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            species = species_name(_obs(context).get("species", ""), "ru")
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🔔 *Новое наблюдение #{obs_id}*\n"
                    f"Вид: {species}\n"
                    f"Дата: {_obs(context).get('date')}\n"
                    f"Пользователь: `{update.effective_user.id}`"  # type: ignore[union-attr]
                ),
                parse_mode="Markdown",
            )
        except Exception:
            pass

    context.user_data.pop("obs", None)  # type: ignore[union-attr]
    context.user_data.pop("editing_field", None)  # type: ignore[union-attr]
    return MAIN_MENU


async def confirm_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    await _log(update, "edit_triggered")

    await query.edit_message_text(
        t(lang, "edit_choose_field"),
        parse_mode="Markdown",
        reply_markup=edit_field_kb(lang),
    )
    return EDITING_FIELD


# ── edit field router ────────────────────────────────────────────────────────

_EDIT_STEP_MAP = {
    "edit_species":       (SELECTING_SPECIES,         "step_species",       species_kb),
    "edit_obs_type":      (SELECTING_OBS_TYPE,         "step_obs_type",      obs_type_kb),
    "edit_photos":        (UPLOADING_PHOTOS,            "step_photos",        photos_kb),
    "edit_date":          (ENTERING_DATE,               "step_date",          None),
    "edit_location":      (SELECTING_LOCATION_METHOD,   "step_location",      location_method_kb),
    "edit_location_name": (ENTERING_LOCATION_NAME,      "step_location_name", skip_kb),
    "edit_observer":      (ENTERING_OBSERVER_NAME,      "step_observer",      anonymous_kb),
    "edit_notes":         (ENTERING_NOTES,              "step_notes",         skip_kb),
}


async def handle_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    action = query.data  # type: ignore[union-attr]

    if action == "back_to_confirmation":
        await _log(update, "edit_cancelled")
        return await _show_confirmation(query.edit_message_text, lang, _obs(context))

    if action == "edit_photos":
        # Reset photos list before re-collecting
        _obs(context)["photos"] = []

    mapping = _EDIT_STEP_MAP.get(action)
    if not mapping:
        return EDITING_FIELD

    next_state, text_key, kb_fn = mapping
    context.user_data["editing_field"] = action.removeprefix("edit_")  # type: ignore[index]
    await _log(update, "edit_field_selected", action.removeprefix("edit_"))

    # For species selection, send individual photo + button per species
    if action == "edit_species":
        await query.edit_message_text(t(lang, text_key), parse_mode="Markdown")
        await _send_species_gallery(query.message.chat_id, context, lang)  # type: ignore[union-attr]
        return next_state

    kb = kb_fn(lang) if kb_fn else None
    await query.edit_message_text(
        t(lang, text_key),
        parse_mode="Markdown",
        reply_markup=kb,
    )
    return next_state
