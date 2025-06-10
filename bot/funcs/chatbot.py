import uuid
from bot.core.common import (
    Common,
    safe_call
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


async def result(text, history, media=None):
    llm_msg = [text]
    if media:
        llm_msg.append(media)
    result = await Common.agent.run(llm_msg, message_history=history)
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


async def continue_chat(client, message, text):
    chat_id = message.chat.id
    message_id = message.reply_to_message.id
    session_id = Common.message_id_hist.get((chat_id, message_id))
    if session_id is None:
        return

    result_dict = {}
    thumb = None
    if message.media:
        mime_type = "application/octet-stream"
        if message.document and message.document.mime_type:
            mime_type = message.document.mime_type
        elif message.photo:
            mime_type = "image/jpeg"
        elif message.audio:
            mime_type = "audio/mpeg"
        elif message.voice:
            mime_type = "audio/ogg"
        elif message.video:
            mime_type = "video/mp4"
        elif message.video_note:
            mime_type = "video/mp4"
        elif message.animation:
            mime_type = "video/mp4"
        elif message.sticker:
            if message.sticker.is_animated:
                thumb = message.sticker.thumbs[0]
                mime_type="image/webp"
            elif message.sticker.is_video:
                mime_type = "video/mp4"
            else:
                mime_type = "image/webp"
        if thumb:
            byte_stream = await client.download_media(thumb.file_id, in_memory=True)
            byte_stream.seek(0)
        else:
            byte_stream = await message.download(in_memory=True)
            byte_stream.seek(0)

        result_dict['media'] = Common.binary(data=byte_stream.getvalue(),media_type=mime_type)

    logging.debug(f"{chat_id} - {session_id}: response - {text}")
    message_history = Common.message_bot_hist[(chat_id, session_id)].get("history")
    result_dict['text'] = text
    result_dict['history'] = message_history

    response = await result(**result_dict)

    logging.debug(f"{chat_id} - {session_id}: message history: {message_history}")
    msg = await safe_call(
        message.reply,
        text=response
    )
    Common.message_id_hist[(chat_id, msg.id)] = session_id


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

