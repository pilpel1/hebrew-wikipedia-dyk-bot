from __future__ import annotations

from datetime import time
import logging

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import Settings
from .wikipedia import DidYouKnowItem, fetch_daily_did_you_know


CAPTION_LIMIT = 1024
TEXT_MESSAGE_LIMIT = 4096
LOGGER = logging.getLogger(__name__)


def build_message(item: DidYouKnowItem) -> str:
    return f"הידעת?\n\n{item.text}\n\nמקור: ויקיפדיה העברית\n{item.source_url}"


def split_text_message(message: str, limit: int = TEXT_MESSAGE_LIMIT) -> list[str]:
    if len(message) <= limit:
        return [message]

    parts = []
    remaining = message
    while len(remaining) > limit:
        minimum_useful_split = limit // 2
        split_at = remaining.rfind("\n\n", 0, limit + 1)
        if split_at < minimum_useful_split:
            split_at = remaining.rfind("\n", 0, limit + 1)
        if split_at < minimum_useful_split:
            split_at = remaining.rfind(" ", 0, limit + 1)
        if split_at < minimum_useful_split:
            split_at = limit

        part = remaining[:split_at].strip()
        if part:
            parts.append(part)
        remaining = remaining[split_at:].strip()

    if remaining:
        parts.append(remaining)

    return parts


async def send_did_you_know(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    item = fetch_daily_did_you_know(settings.user_agent)
    await send_item(context.bot, settings.telegram_channel_id, item)
    LOGGER.info("Sent daily did-you-know item to %s", settings.telegram_channel_id)


async def send_item(bot: Bot, chat_id: str | int, item: DidYouKnowItem) -> None:
    message = build_message(item)
    if item.image_url and len(message) <= CAPTION_LIMIT:
        await bot.send_photo(chat_id=chat_id, photo=item.image_url, caption=message)
        return

    if item.image_url:
        await bot.send_photo(chat_id=chat_id, photo=item.image_url)

    for part in split_text_message(message):
        await bot.send_message(chat_id=chat_id, text=part, disable_web_page_preview=False)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "שלום! אני שולח את ה'הידעת' היומי של ויקיפדיה העברית לערוץ שהוגדר.\n"
        "אפשר לשלוח /today כדי לקבל את הקטע הנוכחי לבדיקה."
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    item = fetch_daily_did_you_know(settings.user_agent)
    await send_item(context.bot, update.effective_chat.id, item)


def build_application(settings: Settings) -> Application:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["settings"] = settings

    if settings.enable_private_commands:
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("today", today))

    hour, minute = settings.hour_minute
    application.job_queue.run_daily(
        send_did_you_know,
        time=time(hour, minute, tzinfo=settings.zoneinfo),
        name="daily_did_you_know",
    )

    return application
