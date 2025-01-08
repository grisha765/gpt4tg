from config.config import Config
from pyrogram import Client, filters #type: ignore

from func.activate import is_activated, generate_password, activate_group
from func.msg import request, request_reply

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
    await activate_group(app, message, text, chat_id)

@app.on_message(filters.command("gpt") & activated_filter)
async def handle_request(_, message):
    text = message.text.split(maxsplit=1)
    await request(app, message, text)

@app.on_message(activated_filter & filters.reply & ~filters.command("gpt"))
async def handle_reply(_, message):
    text = message.text
    await request_reply(app, message, text)

async def start_bot():
    logging.info("Launching the bot...")
    await app.start()

async def stop_bot():
    logging.info("Stopping the bot...")
    await app.stop()

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

