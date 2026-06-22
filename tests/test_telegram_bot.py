import asyncio

from telegram.constants import ParseMode

from wiki_didyouknow_bot.telegram_bot import (
    TEXT_MESSAGE_LIMIT,
    _html_visible_text,
    _telegram_visible_len,
    build_html_message,
    send_item,
    split_html_message,
)
from wiki_didyouknow_bot.wikipedia import DidYouKnowItem


class FakeBot:
    def __init__(self):
        self.calls = []

    async def send_photo(self, **kwargs):
        self.calls.append(("photo", kwargs))

    async def send_message(self, **kwargs):
        self.calls.append(("message", kwargs))


def test_send_item_always_sends_image_separately_from_text():
    bot = FakeBot()
    item = DidYouKnowItem(
        text="טקסט קצר",
        image_url="https://example.com/image.jpg",
        source_url="https://he.wikipedia.org/wiki/ויקיפדיה:הידעת%3F",
        html_text='<a href="https://he.wikipedia.org/wiki/טקסט">טקסט</a> קצר',
    )

    asyncio.run(send_item(bot, "@channel", item))

    assert bot.calls == [
        (
            "photo",
            {
                "chat_id": "@channel",
                "photo": "https://example.com/image.jpg",
            },
        ),
        (
            "message",
            {
                "chat_id": "@channel",
                "text": build_html_message(item),
                "parse_mode": ParseMode.HTML,
                "disable_web_page_preview": True,
            },
        ),
    ]


def test_send_item_sends_long_image_item_as_photo_then_text():
    bot = FakeBot()
    item = DidYouKnowItem(text="א" * 1024, image_url="https://example.com/image.jpg")

    asyncio.run(send_item(bot, "@channel", item))

    assert bot.calls[0] == (
        "photo",
        {
            "chat_id": "@channel",
            "photo": "https://example.com/image.jpg",
        },
    )
    assert bot.calls[1] == (
        "message",
        {
            "chat_id": "@channel",
            "text": build_html_message(item),
            "parse_mode": ParseMode.HTML,
            "disable_web_page_preview": True,
        },
    )
    assert len(bot.calls[1][1]["text"]) <= TEXT_MESSAGE_LIMIT


def test_send_item_splits_text_messages_above_telegram_limit():
    bot = FakeBot()
    item = DidYouKnowItem(text="מילה " * 900, image_url=None)

    asyncio.run(send_item(bot, "@channel", item))

    assert len(bot.calls) == 2
    assert all(call[0] == "message" for call in bot.calls)
    assert all(call[1]["parse_mode"] == ParseMode.HTML for call in bot.calls)
    assert all(_telegram_visible_len(_html_visible_text(call[1]["text"])) <= TEXT_MESSAGE_LIMIT for call in bot.calls)


def test_split_html_message_counts_visible_text_not_hidden_urls():
    long_url = "https://he.wikipedia.org/wiki/" + "a" * TEXT_MESSAGE_LIMIT
    item = DidYouKnowItem(
        text="טקסט קצר",
        image_url=None,
        source_url=long_url,
        html_text=f'<a href="{long_url}">טקסט</a> קצר',
    )

    parts = split_html_message(item)

    assert len(parts) == 1
    assert len(parts[0]) > TEXT_MESSAGE_LIMIT
    assert _telegram_visible_len(_html_visible_text(parts[0])) <= TEXT_MESSAGE_LIMIT


def test_split_html_message_keeps_link_text_together():
    item = DidYouKnowItem(
        text="",
        image_url=None,
        html_text=(
            ("מילה " * 815)
            + '<a href="https://he.wikipedia.org/wiki/ארץ_האש">ארץ האש</a>'
            + " סוף"
        ),
    )

    parts = split_html_message(item)

    assert len(parts) == 2
    assert any('<a href="https://he.wikipedia.org/wiki/ארץ_האש">ארץ האש</a>' in part for part in parts)
    assert all(_telegram_visible_len(_html_visible_text(part)) <= TEXT_MESSAGE_LIMIT for part in parts)
