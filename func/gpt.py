import aiohttp
from config.config import Config
from config import logging_config
logging = logging_config.setup_logging(__name__)

async def gpt_request(text):
    logging.debug(f"GPT Request: {text}")
    url = f"http://{Config.api_ip}:{Config.api_port}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {
                "role": "user",
                "content": text
            }
        ],
        "model": Config.gpt_model,
        "provider": Config.gpt_provider
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                logging.debug(f"GPT Response: {content}")
                return content
            else:
                logging.error(f"Request failed with status code {response.status}\n{await response.text()}")
                return f"Request failed with status code {response.status}"

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
