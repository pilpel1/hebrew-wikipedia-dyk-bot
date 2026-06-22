import asyncio

from wiki_didyouknow_bot.telegram_bot import TEXT_MESSAGE_LIMIT, build_message, send_item
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
    item = DidYouKnowItem(text="טקסט קצר", image_url="https://example.com/image.jpg")

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
                "text": build_message(item),
                "disable_web_page_preview": False,
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
            "text": build_message(item),
            "disable_web_page_preview": False,
        },
    )
    assert len(bot.calls[1][1]["text"]) <= TEXT_MESSAGE_LIMIT


def test_send_item_splits_text_messages_above_telegram_limit():
    bot = FakeBot()
    item = DidYouKnowItem(text="א" * (TEXT_MESSAGE_LIMIT + 200), image_url=None)

    asyncio.run(send_item(bot, "@channel", item))

    assert len(bot.calls) == 2
    assert all(call[0] == "message" for call in bot.calls)
    assert all(len(call[1]["text"]) <= TEXT_MESSAGE_LIMIT for call in bot.calls)
