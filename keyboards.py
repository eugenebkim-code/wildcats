"""All keyboard/button builders in one module."""

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from locales import SPECIES, OBS_TYPES, t


# ── helpers ──────────────────────────────────────────────────────────────────

def _inline(*rows: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Build InlineKeyboardMarkup from list of (text, callback_data) rows."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(txt, callback_data=cb) for txt, cb in row] for row in rows]
    )


# ── keyboards ────────────────────────────────────────────────────────────────

def language_kb() -> InlineKeyboardMarkup:
    return _inline(
        [("🇷🇺 Русский",   "lang_ru")],
        [("🇺🇿 O'zbekcha", "lang_uz")],
        [("🇬🇧 English",   "lang_en")],
    )


def main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    return _inline([(t(lang, "add_observation"), "add_observation")])


def species_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(names[lang], callback_data=f"species_{key}")]
         for key, names in SPECIES.items()]
    )


def obs_type_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(names[lang], callback_data=f"obs_type_{key}")]
         for key, names in OBS_TYPES.items()]
    )


def photos_kb(lang: str) -> InlineKeyboardMarkup:
    return _inline(
        [(t(lang, "photos_done"), "photos_done")],
        [(t(lang, "skip"),        "photos_skip")],
    )


def location_method_kb(lang: str) -> InlineKeyboardMarkup:
    return _inline(
        [(t(lang, "location_current"), "loc_current")],
        [(t(lang, "location_map"),     "loc_map")],
        [(t(lang, "location_manual"),  "loc_manual")],
    )


def geo_request_kb(lang: str) -> ReplyKeyboardMarkup:
    """ReplyKeyboard with a single 'share location' button."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t(lang, "share_location_btn"), request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def skip_kb(lang: str) -> InlineKeyboardMarkup:
    return _inline([(t(lang, "skip"), "skip")])


def anonymous_kb(lang: str) -> InlineKeyboardMarkup:
    return _inline([(t(lang, "anonymous"), "anonymous")])


def confirmation_kb(lang: str) -> InlineKeyboardMarkup:
    return _inline(
        [(t(lang, "btn_send"), "confirm_send")],
        [(t(lang, "btn_edit"), "confirm_edit")],
    )


def edit_field_kb(lang: str) -> InlineKeyboardMarkup:
    return _inline(
        [(t(lang, "edit_species"),       "edit_species")],
        [(t(lang, "edit_obs_type"),      "edit_obs_type")],
        [(t(lang, "edit_photos"),        "edit_photos")],
        [(t(lang, "edit_date"),          "edit_date")],
        [(t(lang, "edit_location"),      "edit_location")],
        [(t(lang, "edit_location_name"), "edit_location_name")],
        [(t(lang, "edit_observer"),      "edit_observer")],
        [(t(lang, "edit_notes"),         "edit_notes")],
        [(t(lang, "back_to_confirmation"), "back_to_confirmation")],
    )
