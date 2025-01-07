import string, random, asyncio
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

queues = {}
processing_tasks = {}
conversations = {}
conv_map = {}

def build_history(conv):
    text = "Chat History:\n"
    for role, content in conv:
        text += f"{role}: {content}\n"
    return text

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

async def process_queue(chat_id):
    while not queues[chat_id].empty():
        req = await queues[chat_id].get()
        msg = req['message']
        q = req['query']
        cid = req['conv_id']
        user_role = req['user_role']
        try:
            await msg.edit_text("Generating...")
            h = build_history(conversations[cid])
            logging.debug(f"Format history: {h}")
            r = await gpt_request(q, history=h)
            conversations[cid].append((user_role, q))
            if len(conversations[cid]) > 10:
                conversations[cid].pop(0)
            conversations[cid].append(("bot", r))
            if len(conversations[cid]) > 10:
                conversations[cid].pop(0)
            await msg.edit_text(r)
            conv_map[msg.id] = cid
        except Exception as e:
            logging.error(f"Error processing GPT request: {e}")
            await msg.edit_text("An error occurred while processing your request.")
    del processing_tasks[chat_id]

@app.on_message(filters.command("gpt") & activated_filter)
async def handle_request(_, message):
    text = message.text.split(maxsplit=1)
    if len(text) <= 1:
        await message.reply("Please enter text after the /gpt command. Example: /gpt Tell me a joke.")
        return
    query = text[1]
    chat_id = message.chat.id
    conv_id = f"{chat_id}_{message.id}"
    if conv_id not in conversations:
        conversations[conv_id] = []
    if chat_id not in queues:
        queues[chat_id] = asyncio.Queue()
    queue = queues[chat_id]
    pos = queue.qsize() + 1
    reply_message = await message.reply(f"Your request is in the queue. Position: {pos}")
    conv_map[reply_message.id] = conv_id
    await queue.put({'query': query, 'message': reply_message, 'conv_id': conv_id, 'user_role': 'user'})
    if chat_id not in processing_tasks:
        processing_tasks[chat_id] = asyncio.create_task(process_queue(chat_id))

@app.on_message(activated_filter & filters.reply & ~filters.command("gpt"))
async def handle_reply(_, message):
    logging.debug(f"Conversations: {conversations}, conv_map: {conv_map}")
    if not message.reply_to_message:
        return
    mid = message.reply_to_message.id
    if mid not in conv_map:
        return
    chat_id = message.chat.id
    conv_id = conv_map[mid]
    q = message.text
    if chat_id not in queues:
        queues[chat_id] = asyncio.Queue()
    queue = queues[chat_id]
    pos = queue.qsize() + 1
    reply_message = await message.reply(f"Your request is in the queue. Position: {pos}")
    conv_map[reply_message.id] = conv_id
    await queue.put({'query': q, 'message': reply_message, 'conv_id': conv_id, 'user_role': 'user'})
    if chat_id not in processing_tasks:
        processing_tasks[chat_id] = asyncio.create_task(process_queue(chat_id))

async def start_bot():
    logging.info("Launching the bot...")
    await app.start()

async def stop_bot():
    logging.info("Stopping the bot...")
    await app.stop()

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

