import pyrogram.filters
import pyrogram.handlers.message_handler
from bot.funcs.activate import is_activated
from bot.funcs.base import (
    new_chat_member,
    activate_group,
    request,
    reply
)

activated_filter = pyrogram.filters.create(is_activated)


def init_handlers(app):
    app.add_handler(
        pyrogram.handlers.message_handler.MessageHandler(
            new_chat_member,
            pyrogram.filters.new_chat_members
        )
    )
    app.add_handler(
        pyrogram.handlers.message_handler.MessageHandler(
            activate_group,
            pyrogram.filters.command("activate") &
                pyrogram.filters.group
        )
    )
    app.add_handler(
        pyrogram.handlers.message_handler.MessageHandler(
            request,
            pyrogram.filters.command("gpt") &
                pyrogram.filters.group &
                activated_filter
        )
    )
    app.add_handler(
        pyrogram.handlers.message_handler.MessageHandler(
            reply,
            ~ pyrogram.filters.command("gpt") &
                pyrogram.filters.group &
                pyrogram.filters.reply &
                activated_filter
        )
    )


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

