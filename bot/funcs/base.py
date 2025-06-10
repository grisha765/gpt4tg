from pyrogram.enums import ParseMode
from bot.funcs.activate import generate_password, activate_chat
from bot.funcs.commands import command_handler
from bot.db.username import set_username, check_username
from bot.core.common import safe_call


async def new_chat_member(client, message):
    chat_id = message.chat.id
    await generate_password(client, chat_id)


async def activate_group(client, message):
    chat_id = message.chat.id
    text = message.text.split(maxsplit=1)
    await activate_chat(client, message, text, chat_id)


async def request(_, message):
    text = message.text.split(maxsplit=1)
    if len(text) <= 1:
        info_text = """
Please enter text after the /gpt command. Example:
<code>/gpt \"system prompt optional\" Tell me a joke.</code> - Create a virtual chat and start communicating with the bot.
<code>/gpt !setname new_username</code> - Change username.
<code>/gpt !analysis</code> - Get chat analysis.
        """
        await safe_call(
            message.reply,
            text=info_text,
            parse_mode=ParseMode.HTML
        )
        return
    username = await check_username(message.from_user.id)
    if username:
        username = username
    else:
        await set_username(message.from_user.id, message.from_user.username if message.from_user.username else message.from_user.first_name)
        username = await check_username(message.from_user.id)

    if text[1].startswith("!"):
        parts = text[1].split(" ", 1)
        command = parts[0]
        args = parts[1:]
        await command_handler(message, username, command, args)
    else:
        await safe_call(
            message.reply,
            text=f"{username} Hello, gpt!"
        )


async def reply(_, message):
    text = message.text
    username = await check_username(message.from_user.id)
    if username:
        username = username
    else:
        await set_username(message.from_user.id, message.from_user.username if message.from_user.username else message.from_user.first_name)
        username = await check_username(message.from_user.id)

    await safe_call(
        message.reply,
        text=f"{username} Hello, gpt reply!"
    )


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

