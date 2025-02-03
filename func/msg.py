import asyncio, re, tempfile, os
from pyrogram.enums import ChatAction, ParseMode
from db.chat import save_message
from config.config import Config
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

def convert_tgs_to_gif(tgs_file: str, gif_file: str):
    from lottie.exporters.gif import export_gif
    from lottie.parsers.tgs import parse_tgs
    with open(tgs_file, "rb") as file:
        lottie_animation = parse_tgs(file)
    export_gif(lottie_animation, gif_file, skip_frames=30)

async def process_queue(app, chat_id, genai=False):
    processed_first_photo = {}
    while not queues[chat_id].empty():
        req = await queues[chat_id].get()
        msg = req['message']
        query = req['query']
        cid = req['conv_id']
        user_role = req['user_role']
        typing_task = await gen_typing(app, chat_id, True)
        media = False
        try:
            system_prompt = conversations[cid].get("system_prompt", "")
            if genai:
                from models.genai import gpt_request
                if msg.photo or msg.animation or msg.sticker or msg.voice:
                    if processed_first_photo.get(user_role, False):
                        logging.warning(f"{cid}: skipping subsequent photo.")
                        continue
                    processed_first_photo[user_role] = True
                    caption = msg.caption if msg.caption else "None"
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    logging.debug(f"{cid}: download media file")
                    await msg.download(temp_file.name)
                    if msg.sticker and msg.sticker.is_animated:
                        convert_tgs_to_gif(temp_file.name, temp_file.name)
                    query = f"Send media: {temp_file.name} text: {caption}"
                    media = temp_file.name
            else:
                from models.gpt import gpt_request
            r = await gpt_request(query, user_role, history=conversations[cid]["history"], systemprompt=system_prompt, media_file=media) #type: ignore
            conversations[cid]["history"].append((user_role, query))
            if len(conversations[cid]["history"]) > Config.chat_msg_storage:
                conversations[cid]["history"].pop(0)
            conversations[cid]["history"].append(("bot", r))
            if len(conversations[cid]["history"]) > Config.chat_msg_storage:
                conversations[cid]["history"].pop(0)
            r_msg = await msg.reply(r[:4096].replace('@', ''), parse_mode=ParseMode.MARKDOWN) #type: ignore
            conv_map[r_msg.id] = cid
        except Exception as e:
            logging.error(f"Error processing GPT request: {e}")
            await msg.reply("Error sending final message.")
        finally:
            await gen_typing(app, chat_id, typing_task)
            if genai:
                if msg.photo or msg.animation or msg.sticker:
                    temp_file.close() #type: ignore
                    if os.path.exists(temp_file.name): #type: ignore
                        logging.debug(f"{cid}: remove media file")
                        os.remove(temp_file.name) #type: ignore

    del processing_tasks[chat_id]

async def request(app, message, text, username, genai=False):
    #logging.debug(f"conv map: {conv_map}")
    #logging.debug(f"conversations: {conversations}")
    full_text = " ".join(text[1:]).strip()
    system_prompt, query = "", ""
    m = re.match(r'^"([^"]+)"\s*(.*)$', full_text, re.DOTALL)
    if m:
        system_prompt = m.group(1).strip()
        query = m.group(2).strip()
    else:
        query = full_text

    if not query:
        await message.reply(
            'Please enter some query text after the system prompt. Example: \n<code>/gpt "system prompt optional" Tell me a joke.</code>',
            parse_mode=ParseMode.HTML
        )
        return

    if message.reply_to_message:
        replied_msg = message.reply_to_message

        replied_text = replied_msg.text or replied_msg.caption
        replied_user = replied_msg.from_user

        if replied_user:
            replied_username = replied_user.username
        elif message.reply_to_message.chat:
            replied_username = replied_msg.chat.title
        else:
            replied_username = replied_user.first_name
        query = f"Reply message: '{replied_username}: {replied_text}', text: {query}"

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
    await queue.put({'query': query, 'message': message, 'conv_id': conv_id, 'user_role': username})
    if chat_id not in processing_tasks:
        processing_tasks[chat_id] = asyncio.create_task(process_queue(app, chat_id, genai=genai))

async def request_reply(app, message, text, username, genai=False):
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
    await queue.put({'query': text, 'message': message, 'conv_id': conv_id, 'user_role': username})
    if chat_id not in processing_tasks:
        processing_tasks[chat_id] = asyncio.create_task(process_queue(app, chat_id, genai=genai))

async def save_messages(message):
    chat_id = message.chat.id
    message_id = message.id
    if message.sender_chat:
        username = message.sender_chat.username
    else:
        username = message.from_user.username or message.from_user.first_name
    message_text = message.text or message.caption
    if message.voice and Config.genai_api:
        from models.genai import gpt_request
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        logging.debug(f"{chat_id}: download media file")
        await message.download(temp_file.name)
        media = temp_file.name
        message_text = await gpt_request(
            "text: None",
            "",
            None,
            {"chat_link_id": None, "type": "voice"},
            media_file=media #type: ignore
        )
        temp_file.close() #type: ignore
        if os.path.exists(media): #type: ignore
            logging.debug(f"{chat_id}: remove media file")
            os.remove(media) #type: ignore
        if "📛" in str(message_text) or message_text == None:
            return
    elif message.media:
        return

    reply_to_message_id = message.reply_to_message.id if message.reply_to_message else None

    if await save_message(chat_id, message_id, username, message_text, reply_to_message_id):
        logging.debug(f"{chat_id}: Message {message_id} saved!")

async def analysis(app, message):
    if Config.genai_api:
        from models.genai import gpt_request
        from db.chat import get_messages
        chat_id = message.chat.id
        if message.chat.username:
            chat_link_id = message.chat.username
            username = True
        else:
            chat_link_id = str(chat_id).replace("-100", "")
            username = False
        text = 'Your task is to briefly analyze this chat.'
        typing_task = await gen_typing(app, chat_id, True)
        history = await get_messages(chat_id)
        resp = await gpt_request(text, "", history, {"chat_link_id": chat_link_id, "type": {"username": username}}, media_file=False)
        await message.reply(resp)
        await gen_typing(app, chat_id, typing_task)
    else:
        await message.reply("Function available only in gemini.")

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
