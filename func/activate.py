import string, random
from db.activate import add_group, activate_group, check_group
from config import logging_config
logging = logging_config.setup_logging(__name__)

async def is_activated(_, __, message):
    chat_id = message.chat.id
    group_info = await check_group(chat_id)
    return group_info["activated"]

async def generate_password(app, chat_id):
    group_info = await check_group(chat_id)
    if group_info["password"] is None:
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        logging.info(f"Group activation password {chat_id}: {password}")
        await add_group(chat_id, password)
        await app.send_message(
            chat_id,
            "This bot requires activation to work, password appeared in the logs.\nEnter the command: /activate password_from_log"
        )

async def activate_chat(app, message, text, chat_id):
    group_info = await check_group(chat_id)

    if group_info["password"] is None:
        await generate_password(app, chat_id)
        return

    if group_info["activated"]:
        await app.send_message(chat_id, "The bot is already activated in this group!")
        return

    if len(text) > 1:
        password = text[1]
    else:
        logging.info(f"Group activation password {chat_id}: {group_info['password']}")
        await app.send_message(chat_id, "Please provide a password. Example: /activate password_from_log")
        return

    if await activate_group(chat_id, password):
        await app.send_message(chat_id, "Bot successfully activated!")
        logging.info(f"{chat_id}: Group successfully activated!")
    else:
        await app.send_message(chat_id, "Invalid password. Try again.")

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
