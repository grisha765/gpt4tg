import pydantic_ai
from typing import Any, Literal, cast
from bot.core.common import (
    Common,
    RotatingGeminiKeyClient,
    RotatingOpenAIKeyClient
)
from bot.tools.web_search import google_search
from bot.tools.fetch_url import (
        open_url,
        open_url_find
)
from bot.config.config import Config


async def init_llm():
    agent_kwargs: dict[str, Any] = {
        'retries': Config.retries,
    }
    if not Config.openai_base_url:
        Common.model = Common.gemini_model(
            model_name=Config.model_name,
            provider=Common.gemini_provider(
                api_key='dummy',
                http_client=RotatingGeminiKeyClient(Config.api_key)
            ),
        )
        categories = (
            'HARM_CATEGORY_SEXUALLY_EXPLICIT',
            'HARM_CATEGORY_HATE_SPEECH',
            'HARM_CATEGORY_HARASSMENT',
            'HARM_CATEGORY_DANGEROUS_CONTENT',
            'HARM_CATEGORY_CIVIC_INTEGRITY',
        )

        agent_kwargs['model_settings'] = Common.gemini_model_settings(
            gemini_safety_settings=[
                Common.gemini_model_safety_settings(
                    category=cast(
                        Literal[
                            'HARM_CATEGORY_SEXUALLY_EXPLICIT',
                            'HARM_CATEGORY_HATE_SPEECH',
                            'HARM_CATEGORY_HARASSMENT',
                            'HARM_CATEGORY_DANGEROUS_CONTENT',
                            'HARM_CATEGORY_CIVIC_INTEGRITY',
                        ],
                        cat,
                    ),
                    threshold='BLOCK_NONE',
                )
                for cat in categories
            ]
        )
    else:
        Common.model = Common.openai_model(
            model_name=Config.model_name,
            provider=Common.openai_provider(
                api_key="dummy",
                base_url=Config.openai_base_url,
                http_client=RotatingOpenAIKeyClient(Config.api_key)
            ),
        )
    Common.agent = pydantic_ai.Agent(
        Common.model,
        tools=[
            pydantic_ai.Tool(google_search),
            pydantic_ai.Tool(open_url),
            pydantic_ai.Tool(open_url_find)
        ],
        **agent_kwargs
    )


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

