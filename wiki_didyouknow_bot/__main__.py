from __future__ import annotations

import argparse
import asyncio
import logging

from telegram import Bot

from .config import load_settings
from .telegram_bot import build_application, build_message, send_item
from .wikipedia import fetch_daily_did_you_know


async def _send_once() -> None:
    settings = load_settings()
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")
    if not settings.telegram_channel_id:
        raise ValueError("TELEGRAM_CHANNEL_ID is required")

    async with Bot(settings.telegram_bot_token) as bot:
        item = fetch_daily_did_you_know(settings.user_agent)
        await send_item(bot, settings.telegram_channel_id, item)


def _preview() -> None:
    settings = load_settings()
    item = fetch_daily_did_you_know(settings.user_agent)
    print(build_message(item))
    if item.image_url:
        print(f"\nImage: {item.image_url}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Telegram bot for Hebrew Wikipedia's daily Did You Know item.")
    parser.add_argument("--preview", action="store_true", help="Print today's item without sending to Telegram.")
    parser.add_argument("--send-once", action="store_true", help="Send today's item once and exit.")
    args = parser.parse_args()

    if args.preview:
        _preview()
        return

    if args.send_once:
        asyncio.run(_send_once())
        return

    settings = load_settings()
    if not settings.telegram_channel_id:
        raise ValueError("TELEGRAM_CHANNEL_ID is required")

    application = build_application(settings)
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
