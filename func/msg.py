import asyncio, re, tempfile, os
from pyrogram.enums import ChatAction, ParseMode
from config import logging_config
logging = logging_config.setup_logging(__name__)

queues = {}
processing_tasks = {}
conversations = {}
conv_map = {}

async def gen_typing(app, chat_id, typing_task):
    async def cycle():
        while True:
            await app.send_chat_action(chat_id, ChatAction.TYPING)
            await asyncio.sleep(4)
    if typing_task == True:
        typing_task = asyncio.create_task(cycle())
        return typing_task
    else:
        typing_task.cancel()
        await app.send_chat_action(chat_id, ChatAction.CANCEL)
        try:
            await typing_task
        except asyncio.CancelledError:
            pass

async def process_queue(app, chat_id, genai=False):
    while not queues[chat_id].empty():
        req = await queues[chat_id].get()
        msg = req['message']
        query = req['query']
        cid = req['conv_id']
        user_role = req['user_role']
        typing_task = await gen_typing(app, chat_id, True)
        try:
            system_prompt = conversations[cid].get("system_prompt", "")
            if genai:
                from models.genai import gpt_request
                if msg.photo or msg.animation or msg.sticker:
                    caption = msg.caption if msg.caption else "None"
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    logging.debug(f"{cid}: download media file")
                    await msg.download(temp_file.name)
                    query = f"Send image: {temp_file.name}" + f" text: {caption}"
            else:
                from models.gpt import gpt_request
            r = await gpt_request(query, user_role, history=conversations[cid]["history"], systemprompt=system_prompt)
            conversations[cid]["history"].append((user_role, query))
            if len(conversations[cid]["history"]) > 10:
                conversations[cid]["history"].pop(0)
            conversations[cid]["history"].append(("bot", r))
            if len(conversations[cid]["history"]) > 10:
                conversations[cid]["history"].pop(0)
            r_msg = await msg.reply(r[:4096].replace('@', '')) #type: ignore
            conv_map[r_msg.id] = cid
        except Exception as e:
            logging.error(f"Error processing GPT request: {e}")
            await msg.reply("Error sending final message.")
        finally:
            await gen_typing(app, chat_id, typing_task)
            if genai:
                if msg.photo or msg.animation or msg.sticker:
                    logging.debug(f"{cid}: remove media file")
                    temp_file.close()
                    os.remove(temp_file.name)

    del processing_tasks[chat_id]

async def request(app, message, text, genai=False):
    #logging.debug(f"conv map: {conv_map}")
    #logging.debug(f"conversations: {conversations}")
    if len(text) <= 1:
        await message.reply(
            'Please enter text after the /gpt command. Example: \n<code>/gpt "prompt optional" Tell me a joke.</code>',
            parse_mode=ParseMode.HTML
        )
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
    logging.debug(f"{chat_id}: request is in the queue. Position: {pos}")
    username = message.from_user.username
    if username:
        user = username
    else:
        user = message.from_user.first_name
    await queue.put({'query': query, 'message': message, 'conv_id': conv_id, 'user_role': user})
    if chat_id not in processing_tasks:
        processing_tasks[chat_id] = asyncio.create_task(process_queue(app, chat_id, genai=genai))

async def request_reply(app, message, text, genai=False):
    #logging.debug(f"reply conv map: {conv_map}")
    #logging.debug(f"reply conversations: {conversations}")
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
    logging.debug(f"{chat_id}: request is in the queue. Position: {pos}")
    username = message.from_user.username
    if username:
        user = username
    else:
        user = message.from_user.first_name
    await queue.put({'query': text, 'message': message, 'conv_id': conv_id, 'user_role': user})
    if chat_id not in processing_tasks:
        processing_tasks[chat_id] = asyncio.create_task(process_queue(app, chat_id, genai=genai))

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
