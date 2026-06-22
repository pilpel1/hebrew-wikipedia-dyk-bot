from __future__ import annotations

from datetime import time
from html import escape
import logging
import re

from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from bs4 import BeautifulSoup, NavigableString, Tag

from .config import Settings
from .wikipedia import DidYouKnowItem, fetch_daily_did_you_know


TEXT_MESSAGE_LIMIT = 4096
LOGGER = logging.getLogger(__name__)


def build_message(item: DidYouKnowItem) -> str:
    return f"הידעת?\n\n{item.text}\n\nמקור: ויקיפדיה העברית"


def build_html_message(item: DidYouKnowItem) -> str:
    title = f'<a href="{escape(item.source_url, quote=True)}">הידעת?</a>'
    text = item.html_text if item.html_text is not None else escape(item.text, quote=False)
    return f"{title}\n\n{text}\n\nמקור: ויקיפדיה העברית"


def split_html_message(item: DidYouKnowItem, limit: int = TEXT_MESSAGE_LIMIT) -> list[str]:
    html_message = build_html_message(item)
    if _telegram_visible_len(_html_visible_text(html_message)) <= limit:
        return [html_message]

    title = f'<a href="{escape(item.source_url, quote=True)}">הידעת?</a>'
    source = "מקור: ויקיפדיה העברית"
    body = item.html_text if item.html_text is not None else escape(item.text, quote=False)

    body_limit = limit - max(
        _telegram_visible_len(_html_visible_text(f"{title}\n\n")),
        _telegram_visible_len(_html_visible_text(f"\n\n{source}")),
    )
    body_parts = _split_html_fragment(body, body_limit)

    messages = []
    for index, part in enumerate(body_parts):
        prefix = f"{title}\n\n" if index == 0 else ""
        suffix = f"\n\n{source}" if index == len(body_parts) - 1 else ""
        messages.append(f"{prefix}{part}{suffix}")

    return messages


def split_text_message(message: str, limit: int = TEXT_MESSAGE_LIMIT) -> list[str]:
    if _telegram_visible_len(message) <= limit:
        return [message]

    parts = []
    remaining = message
    while _telegram_visible_len(remaining) > limit:
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


def _split_html_fragment(html: str, limit: int) -> list[str]:
    tokens = _html_tokens(BeautifulSoup(html, "html.parser"))
    parts = []
    current = []
    current_len = 0

    for html_token, visible_text in tokens:
        token_len = _telegram_visible_len(visible_text)
        if current and current_len + token_len > limit:
            if _is_hebrew_prefix(current[-1][1]):
                prefix = current.pop()
                parts.append("".join(token[0] for token in current).strip())
                current = [prefix]
                current_len = _telegram_visible_len(prefix[1])
            else:
                parts.append("".join(token[0] for token in current).strip())
                current = []
                current_len = 0

        current.append((html_token, visible_text))
        current_len += token_len

    if current:
        parts.append("".join(token[0] for token in current).strip())

    return [part for part in parts if part]


def _html_tokens(node) -> list[tuple[str, str]]:
    tokens = []
    for child in node.children:
        if isinstance(child, NavigableString):
            for token in re.findall(r"\S+\s*", str(child)):
                tokens.append((escape(token, quote=False), token))
            continue

        if not isinstance(child, Tag):
            continue

        if child.name == "a" and child.get("href"):
            html = str(child)
            visible_text = child.get_text("", strip=False)
            if visible_text:
                tokens.append((html, visible_text))
            continue

        tokens.extend(_html_tokens(child))

    return tokens


def _html_visible_text(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text("", strip=False)


def _telegram_visible_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def _is_hebrew_prefix(text: str) -> bool:
    return text.strip() in {"ב", "ל", "ה", "ו", "כ", "מ", "ש"}


async def send_did_you_know(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    item = fetch_daily_did_you_know(settings.user_agent)
    await send_item(context.bot, settings.telegram_channel_id, item)
    LOGGER.info("Sent daily did-you-know item to %s", settings.telegram_channel_id)


async def send_item(bot: Bot, chat_id: str | int, item: DidYouKnowItem) -> None:
    if item.image_url:
        await bot.send_photo(chat_id=chat_id, photo=item.image_url)

    for part in split_html_message(item):
        await bot.send_message(
            chat_id=chat_id,
            text=part,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )


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
