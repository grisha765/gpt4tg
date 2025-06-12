import asyncio, httpx, collections
from itertools import cycle
from typing import cast
from pathlib import Path
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatAction
import pydantic_ai.models.openai
import pydantic_ai.providers.openai
import pydantic_ai.models.gemini
import pydantic_ai.providers.google_gla
from bot.config import logging_config
logging = logging_config.setup_logging(__name__)


class Common:
    client_timeout = httpx.Timeout(30.0)
    client_agent = httpx.AsyncClient(timeout=client_timeout)
    message_bot_hist = {}
    message_id_hist = {}
    locks = collections.defaultdict(asyncio.Lock)
    model: pydantic_ai.models.Model
    agent: pydantic_ai.Agent
    binary = pydantic_ai.BinaryContent
    openai_model = pydantic_ai.models.openai.OpenAIModel
    openai_provider = pydantic_ai.providers.openai.OpenAIProvider
    gemini_model = pydantic_ai.models.gemini.GeminiModel
    gemini_model_settings = pydantic_ai.models.gemini.GeminiModelSettings
    gemini_model_safety_settings = pydantic_ai.models.gemini.GeminiSafetySettings
    gemini_provider = pydantic_ai.providers.google_gla.GoogleGLAProvider
    prompt_file = Path('bot') / 'config' / 'prompt.txt'
    system_prompt = prompt_file.read_text(encoding='utf-8')


class RotatingGeminiKeyClient(httpx.AsyncClient):
    def __init__(self, keys, **kwargs):
        kwargs.setdefault("timeout", Common.client_timeout)
        hooks = kwargs.setdefault("event_hooks", {})
        hooks.setdefault("request", []).append(self._add_header)
        self._keys = cycle(keys)
        super().__init__(**kwargs)
    async def _add_header(self, request: httpx.Request):
        key = next(self._keys)
        logging.debug(f"Use Gemini api key: ...{key[-4:]}")
        request.headers["X-Goog-Api-Key"] = key


class RotatingOpenAIKeyClient(httpx.AsyncClient):
    def __init__(self, keys, **kwargs):
        kwargs.setdefault("timeout", Common.client_timeout)
        hooks = kwargs.setdefault("event_hooks", {})
        hooks.setdefault("request", []).append(self._add_header)
        self._keys = cycle(keys)
        super().__init__(**kwargs)
    async def _add_header(self, request: httpx.Request):
        key = next(self._keys)
        logging.debug(f"Use OpenAI api key: ...{key[-4:]}")
        request.headers.pop("Authorization", None)
        request.headers["Authorization"] = f"Bearer {key}"


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

