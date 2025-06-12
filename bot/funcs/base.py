import re
from pyrogram.enums import ParseMode
from pydantic_ai.exceptions import ModelHTTPError
from bot.funcs.activate import (
    generate_password,
    activate_chat
)
from bot.funcs.commands import command_handler
from bot.funcs.chatbot import (
    init_chat,
    continue_chat
)
from bot.db.username import (
    set_username,
    check_username
)
from bot.core.common import (
    Common,
    safe_call,
    gen_typing
)
from bot.config import logging_config
logging = logging_config.setup_logging(__name__)


async def new_chat_member(client, message):
    chat_id = message.chat.id
    await generate_password(client, chat_id)


async def activate_group(client, message):
    chat_id = message.chat.id
    text = message.text.split(maxsplit=1)
    await activate_chat(client, message, text, chat_id)


async def request(client, message):
    text = message.text.split(maxsplit=1)
    if len(text) <= 1:
        info_text = """
Please enter text after the /gpt command. Example:
<code>/gpt {You're the joker who tells funny jokes.} Tell me a joke.</code> - Create a virtual chat and start communicating with the bot.
<code>/gpt !setname new_username</code> - Change username.

<a href="https://github.com/grisha765/gpt4tg">View Source Code</a>
        """
        await safe_call(
            message.reply,
            text=info_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return
    username = await check_username(message.from_user.id)
    if username:
        username = username
    else:
        await set_username(
            message.from_user.id,
            message.from_user.username if message.from_user.username else message.from_user.first_name
        )
        username = await check_username(message.from_user.id)

    if text[1].startswith("!"):
        parts = text[1].split(" ", 1)
        command = parts[0]
        args = parts[1:]
        await command_handler(message, username, command, args)
    else:
        async with Common.locks[message.chat.id]:
            pattern = r"\{([^}]*)\}\s*(.*)"
            text = ''.join(text[1:]).strip()
            system_prompt = None
            match = re.match(pattern, text)
            if match:
                system_prompt = match.group(1).strip()
                text = match.group(2).strip()
            request = f"{username}: [{text}]"
            typing_task = await gen_typing(client, message.chat.id, True)
            try:
                await init_chat(message, request, system_prompt)
            except ModelHTTPError as e:
                logging.error(f"{message.chat.id}: Agent error on http request {e.status_code}, {e.body}")
                await safe_call(
                    message.reply,
                    text=f"Agent error on http request `{e.status_code}`"
                )
            except Exception as e:
                logging.error(f"{message.chat.id}: {e}")
            finally:
                await gen_typing(client, message.chat.id, typing_task)


async def reply(client, message):
    text = (message.text or message.caption or "")
    username = await check_username(message.from_user.id)
    if username:
        username = username
    else:
        await set_username(
            message.from_user.id,
            message.from_user.username if message.from_user.username else message.from_user.first_name
        )
        username = await check_username(message.from_user.id)

    async with Common.locks[message.chat.id]:
        request = f"{username}: [{text.strip()}]"
        typing_task = await gen_typing(client, message.chat.id, True)
        try:
            await continue_chat(client, message, request)
        except ModelHTTPError as e:
            logging.error(f"{message.chat.id}: Agent error on http request {e.status_code}, {e.body}")
            await safe_call(
                message.reply,
                text=f"Agent error on http request `{e.status_code}`"
            )
        except Exception as e:
            logging.error(f"{message.chat.id}: {e}")
        finally:
            await gen_typing(client, message.chat.id, typing_task)


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

