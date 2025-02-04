from db.username import set_username, check_username, reset_username
from func.msg import analysis

from config import logging_config
logging = logging_config.setup_logging(__name__)

analysis_queue = False

async def command_handler(app, message, username, command, args):
    global analysis_queue
    if command == "!setname":
        user_id = message.from_user.id
        if args and len(args) > 0:
            if args[0] == "reset":
                reset = await reset_username(user_id)
                if reset:
                    await message.reply(f"{username} has cleared his username.")
                    return
            new_username = args[0]
            if await set_username(user_id, new_username):
                await message.reply(f"{username} has set a new username: {new_username}")
            else:
                await message.reply(f"Error set a new username.\nUse only letters and numbers, minimum 5 characters, maximum 32 characters.")
        else:
            await message.reply(f"Your Username: {await check_username(user_id)}") 
    elif command == "!analysis":
        if not analysis_queue:
            analysis_queue = True
            try:
                await analysis(app, message)
            finally:
                analysis_queue = False
        else:
            await message.reply("Wait until the last analysis is over.")
    else:
        await message.reply("Unknown command.")

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
