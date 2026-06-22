from __future__ import annotations

from dataclasses import dataclass
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_channel_id: str
    daily_send_time: str
    timezone: str
    enable_private_commands: bool
    user_agent: str

    @property
    def zoneinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def hour_minute(self) -> tuple[int, int]:
        try:
            hour_text, minute_text = self.daily_send_time.split(":", 1)
            hour = int(hour_text)
            minute = int(minute_text)
        except ValueError as exc:
            raise ValueError("DAILY_SEND_TIME must use HH:MM format, for example 09:00") from exc

        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError("DAILY_SEND_TIME must be a valid 24-hour time, for example 09:00")

        return hour, minute


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_channel_id=os.getenv("TELEGRAM_CHANNEL_ID", "").strip(),
        daily_send_time=os.getenv("DAILY_SEND_TIME", "09:00").strip(),
        timezone=os.getenv("TIMEZONE", "Asia/Jerusalem").strip(),
        enable_private_commands=_bool_env("ENABLE_PRIVATE_COMMANDS", True),
        user_agent=os.getenv("USER_AGENT", "hebrew-wikipedia-dyk-bot/0.1").strip(),
    )
