from bot.db.models import Chat
from tortoise.exceptions import IntegrityError

MAX_MESSAGES_PER_CHAT = 1000


async def save_message(
        chat_id: int,
        message_id: int,
        username: str,
        message_text: str,
        reply_to_message_id: int = 0
) -> bool:
    try:
        messages_count = await Chat.filter(chat_id=chat_id).count()

        if messages_count >= MAX_MESSAGES_PER_CHAT:
            oldest_message = await Chat.filter(chat_id=chat_id).order_by("id").first()
            if oldest_message:
                await oldest_message.delete()

        await Chat.create(
            chat_id=chat_id,
            message_id=message_id,
            username=username,
            message_text=message_text,
            reply_to_message_id=reply_to_message_id
        )
        return True
    except IntegrityError:
        return False


async def get_messages(chat_id: int):
    messages = await Chat.filter(chat_id=chat_id).order_by("message_id")

    if not messages:
        return False

    messages_dict = {msg.message_id: msg for msg in messages}

    return [
        {
            "role": "user",
            "parts": [
                {
                    "text": f"[{msg.message_id}] {msg.username}: {msg.message_text}" +
                            (f"\n ↳ Reply to [{msg.reply_to_message_id}] {messages_dict[msg.reply_to_message_id].username}: {messages_dict[msg.reply_to_message_id].message_text}" 
                             if msg.reply_to_message_id in messages_dict else "")
                }
            ]
        }
        for msg in messages
    ]


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
