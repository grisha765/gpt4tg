from bot.db.username import (
    set_username,
    check_username,
    reset_username
)
from bot.core.common import safe_call
from bot.config import logging_config
logging = logging_config.setup_logging(__name__)


async def command_handler(message, username, command, args):
    if command == "!setname":
        user_id = message.from_user.id
        if args and len(args) > 0:
            if args[0] == "reset":
                reset = await reset_username(user_id)
                if reset:
                    await safe_call(
                        message.reply,
                        text=f"{username} has cleared his username."
                    )
                    return
            new_username = args[0]
            if await set_username(user_id, new_username):
                await safe_call(
                    message.reply,
                    text=f"{username} has set a new username: {new_username}"
                )
            else:
                await safe_call(
                    message.reply,
                    text=f"Error set a new username.\nUse only letters and numbers, minimum 5 characters, maximum 32 characters."
                )
        else:
            await safe_call(
                message.reply,
                text=f"Your Username: {await check_username(user_id)}"
            )
    else:
        await safe_call(
            message.reply,
            text="Unknown command."
        )


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
