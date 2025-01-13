from db.username import set_username, check_username
from config import logging_config
logging = logging_config.setup_logging(__name__)

async def command_handler(message, username, command, args):
    if command == "!setname":
        user_id = message.from_user.id
        if args and len(args) > 0:
            new_username = args[0]
            if await set_username(user_id, new_username):
                await message.reply(f"{username} has set a new username: {new_username}")
            else:
                await message.reply(f"Error set a new username.\nUse only letters and numbers, minimum 5 characters.")
        else:
            await message.reply(f"Your Username: {await check_username(user_id)}") 
    else:
        await message.reply("Unknown command.")

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
