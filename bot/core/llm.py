import pydantic_ai
from bot.core.common import Common
from bot.config.config import Config


async def init_llm():
    if 'gemini' in Config.model_name:
        Common.model = Common.gemini_model(
            model_name=Config.model_name,
            provider=Common.gemini_provider(
                api_key=Config.api_key,
                http_client=Common.client_agent
            ),
        )
    else:
        Common.model = Common.openai_model(
            model_name=Config.model_name,
            provider=Common.openai_provider(
                api_key=Config.api_key,
                base_url=Config.openai_base_url,
                http_client=Common.client_agent
            ),
        )
    Common.agent = pydantic_ai.Agent(
        Common.model,
        system_prompt=Common.system_prompt,
        retries=Config.retries
    )


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

