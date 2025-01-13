import string, random
from func.jsondb import load_database, save_database
from config import logging_config
logging = logging_config.setup_logging(__name__)
activated_groups = load_database()

def is_activated(_, __, message):
    chat_id = message.chat.id
    return str(chat_id) in activated_groups and activated_groups[str(chat_id)]["activated"]

async def generate_password(app, chat_id):
    if str(chat_id) not in activated_groups:
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        logging.info(f"Group activation password {chat_id}: {password}")
        activated_groups[str(chat_id)] = {"activated": False, "password": password}
        save_database(activated_groups)
        await app.send_message(
            chat_id,
            "This bot requires activation to work, password appeared in the logs.\nEnter the command: /activate password_from_log"
        )

    if str(chat_id) not in activated_groups:
async def activate_chat(app, message, text, chat_id):
        await generate_password(app, chat_id)
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

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
