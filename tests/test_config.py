import pytest

from wiki_didyouknow_bot.config import Settings


def test_hour_minute_parses_valid_time():
    settings = Settings("", "", "07:30", "Asia/Jerusalem", True, "test")

    assert settings.hour_minute == (7, 30)


@pytest.mark.parametrize("value", ["24:00", "09:99", "9", "soon"])
def test_hour_minute_rejects_invalid_time(value):
    settings = Settings("", "", value, "Asia/Jerusalem", True, "test")

    with pytest.raises(ValueError):
        settings.hour_minute
