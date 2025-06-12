import uuid, textwrap
import pyrogram.errors
from bot.core.common import (
    Common,
    safe_call
)
from pydantic_ai.messages import ModelRequest, SystemPromptPart
from bot.config.config import Config
from bot.config import logging_config
logging = logging_config.setup_logging(__name__)


def format_message_history(messages):
    def _format_content(obj):
        if hasattr(obj, "media_type"):
            mime = getattr(obj, "media_type", "unknown")
            return f"[binary content: {mime}]"
        if isinstance(obj, list):
            return "[" + ", ".join(_format_content(item) for item in obj) + "]"
        return str(obj)
    def _handle_response(response):
        lines = []
        for part in getattr(response, "parts", []):
            role = "Assistant"
            if hasattr(part, "media_type"):
                content_line = _format_content(part)
            else:
                raw_content = getattr(part, "content", "")
                content_line = _format_content(raw_content)
            lines.append(f"{role}: {content_line}")
        return lines
    def _handle_request(request):
        lines = []
        for part in getattr(request, "parts", []):
            role = part.__class__.__name__.replace("PromptPart", "").lower()
            role = role.capitalize()
            if hasattr(part, "media_type"):
                content_line = _format_content(part)
            else:
                raw_content = getattr(part, "content", "")
                content_line = _format_content(raw_content)
            if role == "System" and len(content_line) > 160:
                content_line = f"{content_line[:80]}...\n{content_line[-80:]}"
            lines.append(f"{role}: {content_line}")
        return lines
    readable_lines = []
    for message in messages:
        message_type = message.__class__.__name__
        if message_type == "ModelRequest":
            readable_lines.extend(_handle_request(message))
        elif message_type == "ModelResponse":
            readable_lines.extend(_handle_response(message))
        else:
            readable_lines.append(f"Unknown message type: {message_type}")
    return "\n".join(readable_lines)


def gen_session(chat_id):
    session_id = uuid.uuid4().hex[:12]
    Common.message_bot_hist[(chat_id, session_id)] = {
        "history": [
            ModelRequest(
                parts=[
                    SystemPromptPart(content=Common.system_prompt)
                ]
            )
        ]
    }
    logging.debug(f"{chat_id}: session {session_id} generated")
    return session_id, Common.message_bot_hist[(chat_id, session_id)]["history"]


async def result(text, history, media=None):
    llm_msg = [text]
    if media:
        llm_msg.append(media)
    for attempt, _ in enumerate(Config.api_key, start=1):
        try:
            result = await Common.agent.run(llm_msg, message_history=history)
            response = result.output
            history.extend(result.new_messages())
            return response
        except:
            logging.warning(f"An error occurred during attempt {attempt}.")
            if attempt == len(Config.api_key):
                raise


async def init_chat(message, text, system_prompt=None):
    chat_id = message.chat.id
    session_id, message_history = gen_session(chat_id)
    logging.debug(f"{chat_id} - {session_id}: response - {text}")
    if system_prompt:
        message_history[0].parts.append(
            SystemPromptPart(content=system_prompt)
        )
        logging.debug(f"{chat_id} - {session_id}: system prompt - {system_prompt}")

    response = await result(text, message_history)
    
    logging.debug(f"{chat_id} - {session_id}: message history: {format_message_history(message_history)}")
    try:
        msg = await safe_call(
            message.reply,
            text=response
        )
        Common.message_id_hist[(chat_id, msg.id)] = session_id
    except pyrogram.errors.MessageTooLong:
        for chunk in textwrap.wrap(
            str(response),
            4096,
            break_long_words=False,
            replace_whitespace=False
        ):
            msg = await safe_call(
                message.reply,
                text=chunk
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

    logging.debug(f"{chat_id} - {session_id}: message history: {format_message_history(message_history)}")
    try:
        msg = await safe_call(
            message.reply,
            text=response
        )
        Common.message_id_hist[(chat_id, msg.id)] = session_id
    except pyrogram.errors.MessageTooLong:
        for chunk in textwrap.wrap(
            str(response),
            4096,
            break_long_words=False,
            replace_whitespace=False
        ):
            msg = await safe_call(
                message.reply,
                text=chunk
            )
            Common.message_id_hist[(chat_id, msg.id)] = session_id


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

