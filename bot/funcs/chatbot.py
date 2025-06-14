import uuid, textwrap, pyrogram.errors, re
from collections import deque
from bot.core.common import (
    Common,
    safe_call
)
from pydantic_ai.messages import (
    ModelRequest,
    SystemPromptPart
)
from bot.config.config import Config
from bot.config import logging_config
logging = logging_config.setup_logging(__name__)


def format_message_history(messages, session_id):
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
                content_line = f"{content_line[:80]}... ...{content_line[-80:]}"
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
    new_content = "\n".join(readable_lines)
    log_path = Common.tmp_path / f"{session_id}.log"
    if log_path.exists():
        old_content = log_path.read_text(encoding='utf-8')
        if new_content.startswith(old_content):
            to_append = new_content[len(old_content):]
            if to_append.startswith("\n"):
                to_append = to_append[1:]
            if to_append:
                with log_path.open("a", encoding="utf-8") as f:
                    f.write("\n" + to_append)
        else:
            log_path.write_text(new_content, encoding='utf-8')
    else:
        log_path.write_text(new_content, encoding='utf-8')
    return new_content


def prepare(text: str) -> str:
    think_open  = "<think>"
    think_close = "</think>"
    pattern = re.compile(rf"{think_open}(.*?){think_close}", re.DOTALL)
    if pattern.search(text):
        logging.debug("Thinking found in the text")
        def to_quote(match: re.Match) -> str:
            inside = match.group(1).strip()
            return "\n".join(f"**> {line}" for line in inside.splitlines())
        return pattern.sub(to_quote, text)
    elif think_close in text:
        logging.debug("Thinking completion found in the text")
        inside, rest = text.split(think_close, 1)
        inside = inside.strip()
        quoted = "\n".join(f"**> {line}" for line in inside.splitlines())
        return quoted + rest
    logging.debug("Thinking not found, skip")
    return text


def gen_session(chat_id):
    session_id = uuid.uuid4().hex[:12]
    Common.message_bot_hist[(chat_id, session_id)] = {
        "system_prompt": [
            ModelRequest(
                parts=[
                    SystemPromptPart(content=Common.system_prompt)
                ]
            )
        ],
        "history": deque(maxlen=Config.history_limit)
    }
    logging.debug(f"{chat_id}: session {session_id} generated")
    return (session_id,
            Common.message_bot_hist[(chat_id, session_id)]["system_prompt"],
            Common.message_bot_hist[(chat_id, session_id)]["history"]
            )


async def result(text, system_prompt, history, media=None):
    llm_msg = [text]
    if media:
        llm_msg.append(media)
    for attempt, _ in enumerate(Config.api_key, start=1):
        try:
            result = await Common.agent.run(llm_msg, message_history=[*system_prompt, *history])
            response = prepare(result.output)
            history.extend(result.new_messages())
            return response
        except:
            logging.warning(f"An error occurred during attempt {attempt}.")
            if attempt == len(Config.api_key):
                raise


async def init_chat(message, text, system_prompt=None):
    chat_id = message.chat.id
    session_id, history_prompt, message_history = gen_session(chat_id)
    logging.debug(f"{chat_id} - {session_id}: response - {text}")
    if system_prompt:
        history_prompt[0].parts.append(
            SystemPromptPart(content=system_prompt)
        )
        logging.debug(f"{chat_id} - {session_id}: system prompt - {system_prompt}")

    response = await result(text, history_prompt, message_history)

    log_history = format_message_history(
        [*history_prompt, *message_history],
        session_id
    )
   #logging.debug(f"{chat_id} - {session_id}: message history: {log_history}")
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
        if message.media_group_id:
            media_group = await message.get_media_group()
            if Common.processed_first_media.get(message.media_group_id):
                logging.debug(f"{chat_id} - {session_id}: skipping subsequent media")
                return
            Common.processed_first_media[message.media_group_id] = True
            message = media_group[0]
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
    history_prompt = Common.message_bot_hist[(chat_id, session_id)].get("system_prompt")
    message_history = Common.message_bot_hist[(chat_id, session_id)].get("history")
    result_dict['text'] = text
    result_dict['system_prompt'] = history_prompt
    result_dict['history'] = message_history

    response = await result(**result_dict)

    log_history = format_message_history(
        [*history_prompt, *message_history],
        session_id
    )
   #logging.debug(f"{chat_id} - {session_id}: message history: {log_history}")
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

