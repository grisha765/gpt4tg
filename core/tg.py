import string, random
from config.config import Config
from pyrogram import Client, filters #type: ignore
from func.jsondb import load_database, save_database
from func.gpt import gpt_request
from config import logging_config
logging = logging_config.setup_logging(__name__)

app = Client("bot", api_id=Config.tg_id, api_hash=Config.tg_hash, bot_token=Config.tg_token)

activated_groups = load_database()

def is_activated(_, __, message):
    chat_id = message.chat.id
    return str(chat_id) in activated_groups and activated_groups[str(chat_id)]["activated"]

activated_filter = filters.create(is_activated)

async def generate_password(chat_id):
    if str(chat_id) not in activated_groups:
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        logging.info(f"Group activation password {chat_id}: {password}")
        activated_groups[str(chat_id)] = {"activated": False, "password": password}
        save_database(activated_groups)
        await app.send_message(
            chat_id,
            "This bot requires activation to work, password appeared in the logs.\nEnter the command: /activate password_from_log"
        )

@app.on_message(filters.new_chat_members)
async def handle_new_chat_member(_, message):
    chat_id = message.chat.id
    await generate_password(chat_id)

@app.on_message(filters.command("activate"))
async def handle_activate_group(_, message):
    chat_id = message.chat.id
    text = message.text.split(maxsplit=1)
    if str(chat_id) not in activated_groups:
        await generate_password(chat_id)
        return

    if activated_groups[str(chat_id)]["activated"]:
        await app.send_message(chat_id, "The bot is already activated in this group!")
        return
    if len(text) > 1:
        password = text[1]
    else:
        logging.info(f"Group activation password {chat_id}: {activated_groups[str(chat_id)]["password"]}")
        await app.send_message(chat_id, "Please provide a password. Example: /activate password_from_log")
        return

    if activated_groups[str(chat_id)]["password"] == password:
        activated_groups[str(chat_id)]["activated"] = True
        save_database(activated_groups)
        await app.send_message(chat_id, "Bot successfully activated!")
        logging.info(f"{chat_id}: Group successfully activated!")
    else:
        await app.send_message(chat_id, "Invalid password. Try again.")

@app.on_message(filters.command("gpt") & activated_filter)
async def handle_request(_, message):
    text = message.text.split(maxsplit=1)
    if len(text) > 1:
        query = text[1]
    else:
        await message.reply("Please enter text after the /gpt query.")
        return
    response = await gpt_request(query)
    await message.reply(response)

async def start_bot():
    logging.info("Launching the bot...")
    await app.start()

async def stop_bot():
    logging.info("Stopping the bot...")
    await app.stop()

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

