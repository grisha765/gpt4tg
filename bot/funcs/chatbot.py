import uuid
from bot.core.common import (
    Common,
    safe_call,
)
from bot.config import logging_config
logging = logging_config.setup_logging(__name__)


def gen_session(chat_id):
    session_id = uuid.uuid4().hex[:12]
    Common.message_bot_hist[(chat_id, session_id)] = {
        "history": []
    }
    logging.debug(f"{chat_id}: session {session_id} generated")
    return session_id, Common.message_bot_hist[(chat_id, session_id)]["history"]


async def result(text, history):
    result = await Common.agent.run(text, message_history=history)
    response = result.output
    history.extend(result.new_messages())
    return response


async def init_chat(message, text):
    chat_id = message.chat.id
    session_id, message_history = gen_session(chat_id)
    logging.debug(f"{chat_id} - {session_id}: response - {text}")
    response = await result(text, message_history)
    logging.debug(f"{chat_id} - {session_id}: message history: {message_history}")
    msg = await safe_call(
        message.reply,
        text=response
    )
    Common.message_id_hist[(chat_id, msg.id)] = session_id


async def continue_chat(message, text):
    chat_id = message.chat.id
    message_id = message.reply_to_message.id
    session_id = Common.message_id_hist.get((chat_id, message_id))
    if session_id is None:
        return
    logging.debug(f"{chat_id} - {session_id}: response - {text}")
    message_history = Common.message_bot_hist[(chat_id, session_id)].get("history")
    response = await result(text, message_history)
    logging.debug(f"{chat_id} - {session_id}: message history: {message_history}")
    msg = await safe_call(
        message.reply,
        text=response
    )
    Common.message_id_hist[(chat_id, msg.id)] = session_id


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

