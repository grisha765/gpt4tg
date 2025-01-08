import asyncio, re
from func.gpt import gpt_request
from config import logging_config
logging = logging_config.setup_logging(__name__)

queues = {}
processing_tasks = {}
conversations = {}
conv_map = {}

def build_history(conv):
    text = "Chat History:\n"
    for role, content in conv["history"]:
        text += f"{role}: {content}\n"
    return text

async def process_queue(chat_id):
    while not queues[chat_id].empty():
        req = await queues[chat_id].get()
        msg = req['message']
        query = req['query']
        cid = req['conv_id']
        user_role = req['user_role']
        try:
            await msg.edit_text("Generating...")
            h = build_history(conversations[cid])
            logging.debug(f"Format history: {h}")
            system_prompt = conversations[cid].get("system_prompt", "")
            r = await gpt_request(query, user_role, history=h, systemprompt=system_prompt)
            conversations[cid]["history"].append((user_role, query))
            if len(conversations[cid]["history"]) > 10:
                conversations[cid]["history"].pop(0)
            conversations[cid]["history"].append(("bot", r))
            if len(conversations[cid]["history"]) > 10:
                conversations[cid]["history"].pop(0)
            await msg.edit_text(r)
            conv_map[msg.id] = cid
        except Exception as e:
            logging.error(f"Error processing GPT request: {e}")
            await msg.edit_text("An error occurred while processing your request.")
    del processing_tasks[chat_id]

async def request(message, text):
    if len(text) <= 1:
        await message.reply("Please enter text after the /gpt command. Example: /gpt Tell me a joke.")
        return
    system_prompt, query = "", text[1]
    m = re.match(r'^"([^"]+)"(.*)$', query)
    if m:
        system_prompt = m.group(1).strip()
        query = m.group(2).strip() if m.group(2) else ""
    chat_id = message.chat.id
    conv_id = f"{chat_id}_{message.id}"
    if conv_id not in conversations:
        conversations[conv_id] = {"system_prompt": system_prompt, "history": []}
    if not conversations[conv_id].get("system_prompt"):
        conversations[conv_id]["system_prompt"] = system_prompt
    if chat_id not in queues:
        queues[chat_id] = asyncio.Queue()
    queue = queues[chat_id]
    pos = queue.qsize() + 1
    reply_message = await message.reply(f"Your request is in the queue. Position: {pos}")
    conv_map[reply_message.id] = conv_id
    username = message.from_user.username
    if username:
        user = username
    else:
        user = message.from_user.first_name
    await queue.put({'query': query, 'message': reply_message, 'conv_id': conv_id, 'user_role': user})
    if chat_id not in processing_tasks:
        processing_tasks[chat_id] = asyncio.create_task(process_queue(chat_id))

async def request_reply(message, text):
    if not message.reply_to_message:
        return
    mid = message.reply_to_message.id
    if mid not in conv_map:
        return
    chat_id = message.chat.id
    conv_id = conv_map[mid]
    if chat_id not in queues:
        queues[chat_id] = asyncio.Queue()
    queue = queues[chat_id]
    pos = queue.qsize() + 1
    reply_message = await message.reply(f"Your request is in the queue. Position: {pos}")
    conv_map[reply_message.id] = conv_id
    username = message.from_user.username
    if username:
        user = username
    else:
        user = message.from_user.first_name
    await queue.put({'query': text, 'message': reply_message, 'conv_id': conv_id, 'user_role': user})
    if chat_id not in processing_tasks:
        processing_tasks[chat_id] = asyncio.create_task(process_queue(chat_id))

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
