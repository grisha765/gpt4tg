from config.config import Config
from pyrogram import Client, filters #type: ignore
from pyrogram.enums import ParseMode

from func.activate import is_activated, generate_password, activate_chat
from func.msg import request, request_reply
from func.gpt_commands import command_handler
from db.username import set_username, check_username
from db.chat import save_message

from config import logging_config
logging = logging_config.setup_logging(__name__)

app = Client("bot", api_id=Config.tg_id, api_hash=Config.tg_hash, bot_token=Config.tg_token)

activated_filter = filters.create(is_activated)

@app.on_message(filters.new_chat_members)
async def handle_new_chat_member(_, message):
    chat_id = message.chat.id
    await generate_password(app, chat_id)

@app.on_message(filters.command("activate"))
async def handle_activate_group(_, message):
    chat_id = message.chat.id
    text = message.text.split(maxsplit=1)
    await activate_chat(app, message, text, chat_id)

@app.on_message(filters.command("gpt") & activated_filter)
async def handle_request(_, message):
    text = message.text.split(maxsplit=1)
    if len(text) <= 1:
        await message.reply(
            'Please enter text after the /gpt command. Example: \n<code>/gpt "system prompt optional" Tell me a joke.</code> - Create a virtual chat and start communicating with the bot.\n<code>/gpt !setname new_username</code> - Change username.\n<code>/gpt !analysis</code> - Get chat analysis.',
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
        await command_handler(app, message, username, command, args)
    else:
        await request(app, message, text, username, genai=Config.genai_api)

@app.on_message(activated_filter & ~filters.media & ~filters.command("gpt"))
async def handle_save_message(_, message):
    if message.reply_to_message and message.reply_to_message.from_user.is_bot:
        await handle_reply(_, message)
        return

    chat_id = message.chat.id
    message_id = message.id
    username = message.from_user.username or message.from_user.first_name
    message_text = message.text
    reply_to_message_id = message.reply_to_message.id if message.reply_to_message else None

    if await save_message(chat_id, message_id, username, message_text, reply_to_message_id):
        logging.debug(f"{chat_id}: Message {message_id} saved!")

@app.on_message(activated_filter & filters.reply & ~filters.command("gpt"))
async def handle_reply(_, message):
    text = message.text
    username = await check_username(message.from_user.id)
    if username:
        username = username
    else:
        await set_username(message.from_user.id, message.from_user.username if message.from_user.username else message.from_user.first_name)
        username = await check_username(message.from_user.id)

    await request_reply(app, message, text, username, genai=Config.genai_api)

async def start_bot():
    logging.info("Launching the bot...")
    await app.start()

async def stop_bot():
    logging.info("Stopping the bot...")
    await app.stop()

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

