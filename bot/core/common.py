import asyncio, httpx
from typing import cast
from pathlib import Path
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatAction
import pydantic_ai.models.openai
import pydantic_ai.providers.openai
import pydantic_ai.models.gemini
import pydantic_ai.providers.google_gla


class Common:
    client_timeout = httpx.Timeout(30.0)
    client_agent = httpx.AsyncClient(timeout=client_timeout)
    message_bot_hist = {}
    message_id_hist = {}
    model: pydantic_ai.models.Model
    agent: pydantic_ai.Agent
    openai_model = pydantic_ai.models.openai.OpenAIModel
    openai_provider = pydantic_ai.providers.openai.OpenAIProvider
    gemini_model = pydantic_ai.models.gemini.GeminiModel
    gemini_provider = pydantic_ai.providers.google_gla.GoogleGLAProvider
    prompt_file = Path('bot') / 'config' / 'prompt.txt'
    system_prompt = prompt_file.read_text(encoding='utf-8')


async def safe_call(func, *args, **kwargs):
    for _ in range(5):
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            wait_sec: int = cast(int, e.value)
            await asyncio.sleep(wait_sec + 1)
    raise


async def gen_typing(client, chat_id, typing_task):
    async def cycle():
        while True:
            await client.send_chat_action(chat_id, ChatAction.TYPING)
            await asyncio.sleep(4)
    if typing_task == True:
        typing_task = asyncio.create_task(cycle())
        return typing_task
    else:
        typing_task.cancel()
        await client.send_chat_action(chat_id, ChatAction.CANCEL)
        try:
            await typing_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

