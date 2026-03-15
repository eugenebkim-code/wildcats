"""Admin-only command handlers (accessible outside the ConversationHandler)."""

import io
import json
import csv

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from database import (
    count_observations,
    count_observations_filtered,
    delete_observation,
    get_available_months,
    get_available_years,
    get_observation,
    get_observations,
    get_observations_filtered,
    get_stats,
    update_status,
)
from locales import obs_type_name, species_name


# ── guard ────────────────────────────────────────────────────────────────────

def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _status_icon(status: str) -> str:
    return {"pending": "⏳", "verified": "✅", "doubtful": "⚠️"}.get(status, "❓")


# ── /admin ───────────────────────────────────────────────────────────────────

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return

    s = get_stats()
    text = (
        "🛡 *Административная панель*\n\n"
        f"📊 Всего наблюдений: *{s['total']}*\n"
        f"✅ Подтверждено: *{s['verified']}*\n"
        f"⏳ Ожидает: *{s['pending']}*\n"
        f"⚠️ Сомнительных: *{s['doubtful']}*\n"
        f"👥 Пользователей: *{s['users']}*\n\n"
        "📋 Команды:\n"
        "`/list [стр]` — список наблюдений\n"
        "`/obs <id>` — детали + фото\n"
        "`/verify <id>` — подтвердить\n"
        "`/doubt <id>` — отметить сомнительным\n"
        "`/export` — выгрузить CSV\n"
        "`/history` — история наблюдений\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")  # type: ignore[union-attr]


# ── /list ────────────────────────────────────────────────────────────────────

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return

    page = int(context.args[0]) if context.args else 1  # type: ignore[index]
    limit = 10
    offset = (page - 1) * limit
    total = count_observations()
    observations = get_observations(limit=limit, offset=offset)

    if not observations:
        await update.message.reply_text("Наблюдений нет.")  # type: ignore[union-attr]
        return

    lines = [f"📋 *Наблюдения* (стр. {page}, всего {total})\n"]
    for obs in observations:
        icon = _status_icon(obs["status"])
        sp = species_name(obs["species"], "ru")
        loc = obs.get("location_name") or f"{obs.get('latitude','?')}, {obs.get('longitude','?')}"
        lines.append(f"{icon} *#{obs['id']}* — {sp} | {obs['date']} | {loc}")

    lines.append(f"\n/obs <id> — подробности")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")  # type: ignore[union-attr]


# ── /obs ─────────────────────────────────────────────────────────────────────

async def obs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return

    if not context.args:  # type: ignore[union-attr]
        await update.message.reply_text("Использование: `/obs <id>`", parse_mode="Markdown")  # type: ignore[union-attr]
        return

    try:
        obs_id = int(context.args[0])  # type: ignore[index]
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")  # type: ignore[union-attr]
        return

    obs = get_observation(obs_id)
    if not obs:
        await update.message.reply_text(f"Наблюдение #{obs_id} не найдено.")  # type: ignore[union-attr]
        return

    photos = json.loads(obs.get("photos", "[]"))
    status_labels = {"pending": "⏳ Ожидает", "verified": "✅ Подтверждено", "doubtful": "⚠️ Сомнительное"}

    text = (
        f"🔍 *Наблюдение #{obs['id']}*\n\n"
        f"Статус: {status_labels.get(obs['status'], obs['status'])}\n"
        f"🐱 Вид: {species_name(obs['species'], 'ru')}\n"
        f"📋 Тип: {obs_type_name(obs['observation_type'], 'ru')}\n"
        f"📅 Дата: {obs['date']}\n"
        f"📍 Координаты: {obs.get('latitude', '—')}, {obs.get('longitude', '—')}\n"
        f"🏔 Местность: {obs.get('location_name') or '—'}\n"
        f"👤 Наблюдатель: {obs.get('observer_name') or '—'}\n"
        f"📝 Примечания: {obs.get('notes') or '—'}\n"
        f"📸 Фото: {len(photos)} шт.\n"
        f"🕐 Получено: {obs['created_at']}\n"
        f"🆔 Telegram ID: `{obs['telegram_id']}`\n"
        f"🌐 Язык: {obs.get('language', '—')}"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Подтвердить",   callback_data=f"adm_verify_{obs_id}"),
        InlineKeyboardButton("⚠️ Сомнительное", callback_data=f"adm_doubt_{obs_id}"),
    ]])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)  # type: ignore[union-attr]

    # Attach photos
    for file_id in photos[:10]:
        try:
            await update.message.reply_photo(file_id)  # type: ignore[union-attr]
        except Exception as exc:
            await update.message.reply_text(f"⚠️ Не удалось загрузить фото: {exc}")  # type: ignore[union-attr]


# ── /verify & /doubt ─────────────────────────────────────────────────────────

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return
    if not context.args:  # type: ignore[union-attr]
        await update.message.reply_text("Использование: `/verify <id>`", parse_mode="Markdown")  # type: ignore[union-attr]
        return
    obs_id = int(context.args[0])  # type: ignore[index]
    update_status(obs_id, "verified")
    await update.message.reply_text(f"✅ Наблюдение #{obs_id} подтверждено.")  # type: ignore[union-attr]


async def doubt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return
    if not context.args:  # type: ignore[union-attr]
        await update.message.reply_text("Использование: `/doubt <id>`", parse_mode="Markdown")  # type: ignore[union-attr]
        return
    obs_id = int(context.args[0])  # type: ignore[index]
    update_status(obs_id, "doubtful")
    await update.message.reply_text(f"⚠️ Наблюдение #{obs_id} отмечено как сомнительное.")  # type: ignore[union-attr]


# ── /export ───────────────────────────────────────────────────────────────────

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return

    await update.message.reply_text("⏳ Формирую CSV…")  # type: ignore[union-attr]
    observations = get_observations(limit=100_000)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "date", "species", "species_ru", "observation_type",
        "latitude", "longitude", "location_name",
        "observer_name", "telegram_id", "photos_count",
        "status", "language", "notes", "created_at",
    ])
    for obs in observations:
        photos = json.loads(obs.get("photos", "[]"))
        writer.writerow([
            obs["id"],
            obs["date"],
            obs["species"],
            species_name(obs["species"], "ru"),
            obs["observation_type"],
            obs.get("latitude", ""),
            obs.get("longitude", ""),
            obs.get("location_name", ""),
            obs.get("observer_name", ""),
            obs["telegram_id"],
            len(photos),
            obs["status"],
            obs.get("language", ""),
            obs.get("notes", ""),
            obs["created_at"],
        ])

    csv_bytes = buf.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility
    await update.message.reply_document(  # type: ignore[union-attr]
        document=io.BytesIO(csv_bytes),
        filename="wildcat_observations.csv",
        caption=f"📊 Экспорт: {len(observations)} наблюдений",
    )


# ── inline button callbacks (verify / doubt from /obs message) ───────────────

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not _is_admin(query.from_user.id):
        return

    data: str = query.data  # type: ignore[assignment]
    if data.startswith("adm_verify_"):
        obs_id = int(data.split("_")[-1])
        update_status(obs_id, "verified")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"✅ Наблюдение #{obs_id} подтверждено.")  # type: ignore[union-attr]
    elif data.startswith("adm_doubt_"):
        obs_id = int(data.split("_")[-1])
        update_status(obs_id, "doubtful")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"⚠️ Наблюдение #{obs_id} отмечено как сомнительное.")  # type: ignore[union-attr]


# ── /history ──────────────────────────────────────────────────────────────────

_MONTH_NAMES_RU = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]

PAGE_SIZE = 10


def _history_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Сегодня",       callback_data="hist:today:0")],
        [InlineKeyboardButton("📆 Эта неделя",    callback_data="hist:week:0")],
        [InlineKeyboardButton("🗓 Этот месяц",    callback_data="hist:month:0")],
        [InlineKeyboardButton("🗂 Выбрать месяц", callback_data="hist:years")],
    ])


def _year_kb(years: list[int]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(str(y), callback_data=f"hist:year:{y}")] for y in years]
    rows.append([InlineKeyboardButton("« Назад", callback_data="hist:menu")])
    return InlineKeyboardMarkup(rows)


def _month_kb(year: int, months: list[int]) -> InlineKeyboardMarkup:
    rows = []
    row: list[InlineKeyboardButton] = []
    for m in months:
        row.append(InlineKeyboardButton(_MONTH_NAMES_RU[m], callback_data=f"hist:{year}-{m:02d}:0"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("« Назад", callback_data="hist:years")])
    return InlineKeyboardMarkup(rows)


def _list_kb(filter_str: str, page: int, total: int) -> InlineKeyboardMarkup:
    """Pagination row + Back button."""
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"hist:{filter_str}:{page - 1}"))
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    nav.append(InlineKeyboardButton(f"{page + 1}/{pages}", callback_data="hist:noop"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"hist:{filter_str}:{page + 1}"))

    back_target = "hist:years" if (len(filter_str) == 7 and filter_str[4] == "-") else "hist:menu"
    return InlineKeyboardMarkup([
        nav,
        [InlineKeyboardButton("« Назад", callback_data=back_target)],
    ])


def _obs_summary_line(obs: dict) -> str:
    icon = _status_icon(obs["status"])
    sp = species_name(obs["species"], "ru")
    photos = json.loads(obs.get("photos", "[]"))
    photo_tag = f" 📸{len(photos)}" if photos else ""
    loc = obs.get("location_name") or (
        f"{obs.get('latitude'):.4f}, {obs.get('longitude'):.4f}"
        if obs.get("latitude") is not None else "—"
    )
    return f"{icon} *#{obs['id']}* {sp} | {obs['date']} | {loc}{photo_tag}"


def _obs_detail_text(obs: dict) -> str:
    status_labels = {"pending": "⏳ Ожидает", "verified": "✅ Подтверждено", "doubtful": "⚠️ Сомнительное"}
    photos = json.loads(obs.get("photos", "[]"))
    return (
        f"🔍 *Наблюдение #{obs['id']}*\n\n"
        f"Статус: {status_labels.get(obs['status'], obs['status'])}\n"
        f"🐱 Вид: {species_name(obs['species'], 'ru')}\n"
        f"📋 Тип: {obs_type_name(obs['observation_type'], 'ru')}\n"
        f"📅 Дата: {obs['date']}\n"
        f"📍 Координаты: {obs.get('latitude', '—')}, {obs.get('longitude', '—')}\n"
        f"🏔 Местность: {obs.get('location_name') or '—'}\n"
        f"👤 Наблюдатель: {obs.get('observer_name') or '—'}\n"
        f"📝 Примечания: {obs.get('notes') or '—'}\n"
        f"📸 Фото: {len(photos)} шт.\n"
        f"🕐 Получено: {obs['created_at']}\n"
        f"🆔 Telegram ID: `{obs['telegram_id']}`\n"
        f"🌐 Язык: {obs.get('language', '—')}"
    )


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return
    await update.message.reply_text(  # type: ignore[union-attr]
        "📚 *История наблюдений*\nВыберите период:",
        parse_mode="Markdown",
        reply_markup=_history_menu_kb(),
    )


async def history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not _is_admin(query.from_user.id):
        return

    data: str = query.data  # type: ignore[assignment]
    # data format: "hist:<action_or_filter>:<extra>"
    parts = data.split(":", 2)
    # parts[0] == "hist"
    action = parts[1] if len(parts) > 1 else ""
    extra  = parts[2] if len(parts) > 2 else ""

    # ── no-op (page counter tap) ──────────────────────────────────────────────
    if action == "noop":
        return

    # ── back to filter menu ───────────────────────────────────────────────────
    if action == "menu":
        await query.edit_message_text(
            "📚 *История наблюдений*\nВыберите период:",
            parse_mode="Markdown",
            reply_markup=_history_menu_kb(),
        )
        return

    # ── year selector ─────────────────────────────────────────────────────────
    if action == "years":
        years = get_available_years()
        if not years:
            await query.edit_message_text("Наблюдений пока нет.", reply_markup=_history_menu_kb())
            return
        await query.edit_message_text(
            "📅 Выберите год:",
            reply_markup=_year_kb(years),
        )
        return

    # ── month selector for a specific year ───────────────────────────────────
    if action == "year":
        year = int(extra)
        months = get_available_months(year)
        if not months:
            await query.edit_message_text(
                f"В {year} году наблюдений нет.",
                reply_markup=_year_kb(get_available_years()),
            )
            return
        await query.edit_message_text(
            f"🗓 Выберите месяц ({year}):",
            reply_markup=_month_kb(year, months),
        )
        return

    # ── observation detail view ───────────────────────────────────────────────
    if action == "obs":
        obs_id = int(extra)
        obs = get_observation(obs_id)
        if not obs:
            await query.edit_message_text(f"Наблюдение #{obs_id} не найдено.")
            return

        photos = json.loads(obs.get("photos", "[]"))
        detail_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Подтвердить",   callback_data=f"adm_verify_{obs_id}"),
                InlineKeyboardButton("⚠️ Сомнительное", callback_data=f"adm_doubt_{obs_id}"),
            ],
            [InlineKeyboardButton("🗑 Удалить", callback_data=f"hist:del:{obs_id}")],
            [InlineKeyboardButton("« Назад к списку", callback_data=f"hist:back:{obs_id}")],
        ])
        await query.edit_message_text(
            _obs_detail_text(obs),
            parse_mode="Markdown",
            reply_markup=detail_kb,
        )
        # Send photos as separate messages (can't embed in text message)
        for file_id in photos[:10]:
            try:
                await query.message.reply_photo(file_id)  # type: ignore[union-attr]
            except Exception as exc:
                await query.message.reply_text(f"⚠️ Не удалось загрузить фото: {exc}")  # type: ignore[union-attr]
        return

    # ── delete confirmation prompt ────────────────────────────────────────────
    if action == "del":
        obs_id = int(extra)
        obs = get_observation(obs_id)
        if not obs:
            await query.edit_message_text(f"Наблюдение #{obs_id} не найдено.")
            return
        sp = species_name(obs["species"], "ru")
        confirm_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, удалить",  callback_data=f"hist:delconfirm:{obs_id}"),
                InlineKeyboardButton("❌ Отмена",       callback_data=f"hist:obs:{obs_id}"),
            ],
        ])
        await query.edit_message_text(
            f"⚠️ *Удалить наблюдение #{obs_id}?*\n{sp} | {obs['date']}\n\nЭто действие необратимо.",
            parse_mode="Markdown",
            reply_markup=confirm_kb,
        )
        return

    # ── confirmed delete ──────────────────────────────────────────────────────
    if action == "delconfirm":
        obs_id = int(extra)
        delete_observation(obs_id)
        filter_str = context.user_data.get("hist_filter", "month")  # type: ignore[union-attr]
        page       = context.user_data.get("hist_page", 0)          # type: ignore[union-attr]
        # Reload list after deletion — reuse the list-rendering path
        action = filter_str
        extra  = str(page)
        # fall through to paginated list rendering below

    # ── back from detail to list (stored filter in context) ──────────────────
    if action == "back":
        # extra == obs_id; retrieve saved filter from user_data
        filter_str = context.user_data.get("hist_filter", "month")  # type: ignore[union-attr]
        page       = context.user_data.get("hist_page", 0)          # type: ignore[union-attr]
        action = filter_str
        extra  = str(page)
        # fall through to paginated list rendering below

    # ── paginated observation list ────────────────────────────────────────────
    # action is one of: today / week / month / YYYY-MM
    filter_str = action
    try:
        page = int(extra)
    except (ValueError, TypeError):
        page = 0

    # Persist for "back" navigation
    context.user_data["hist_filter"] = filter_str  # type: ignore[index]
    context.user_data["hist_page"]   = page        # type: ignore[index]

    total = count_observations_filtered(filter_str)
    observations = get_observations_filtered(filter_str, limit=PAGE_SIZE, offset=page * PAGE_SIZE)

    filter_labels = {
        "today": "сегодня",
        "week":  "эта неделя",
        "month": "этот месяц",
    }
    label = filter_labels.get(filter_str, filter_str)

    if not observations:
        await query.edit_message_text(
            f"За период *{label}* наблюдений нет.",
            parse_mode="Markdown",
            reply_markup=_history_menu_kb(),
        )
        return

    lines = [f"📋 *Наблюдения — {label}* (всего {total})\n"]
    obs_buttons: list[InlineKeyboardButton] = []
    for obs in observations:
        lines.append(_obs_summary_line(obs))
        obs_buttons.append(
            InlineKeyboardButton(f"#{obs['id']}", callback_data=f"hist:obs:{obs['id']}")
        )

    # Arrange observation buttons in rows of 5
    obs_rows = [obs_buttons[i:i + 5] for i in range(0, len(obs_buttons), 5)]
    nav_kb = _list_kb(filter_str, page, total)

    keyboard = InlineKeyboardMarkup(obs_rows + list(nav_kb.inline_keyboard))

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
