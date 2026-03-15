"""Admin-only command handlers (accessible outside the ConversationHandler)."""

import io
import json
import csv

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from database import (
    count_observations,
    get_observation,
    get_observations,
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
