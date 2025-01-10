import aiohttp, asyncio
from config.config import Config
from config import logging_config
logging = logging_config.setup_logging(__name__)

async def gpt_request(text, username, history, systemprompt, media_file=False):
    logging.debug(f"GPT Request: {text}")
    logging.debug(f"GPT Chat History: {history}")
    url = f"http://{Config.api_ip}:{Config.api_port}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    messages = []
    #if systemprompt:
    logging.debug(f"GPT Prompt: {systemprompt}")
    messages.append({
        "role": "system",
        "content": f"In this chat, the user marks his nickname before the colon. For example, if a user writes: '{username}: Hello! then '{username}' is a nickname, and 'Hello!' - the message itself. You don't have to write this nickname at the beginning.\n{systemprompt}"
    })

    for user_text, message_text in history:
        if user_text == 'bot':
            messages.append({
                "role": "assistant",
                "content": message_text
            })
        else:
            messages.append({
                "role": "user",
                "content": f"{user_text}: {message_text}"
            })

    messages.append({
        "role": "user",
        "content": f"{username}: {text}"
    })

    logging.debug(f"Messages tuples: {messages}")

    payload = {
        "messages": messages,
        "model": Config.gpt_model,
        "provider": Config.gpt_provider,
        "stop": ["#####"],
        "max_tokens": Config.gpt_tokens,
        "temperature": Config.gpt_temperature
    }

    max_retries = 3
    retry_delay = 15  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        logging.debug(f"GPT Response: {content}")
                        return content
                    elif response.status == 500:
                        logging.warning(f"Attempt {attempt} failed with status code 500. Retrying in {retry_delay} seconds...")
                        if attempt < max_retries:
                            await asyncio.sleep(retry_delay)
                        else:
                            logging.error("Max retries reached. Request failed.")
                            return "📛 Request failed after maximum retries with status code 500."
                    else:
                        logging.error(f"Request failed with status code {response.status}\n{await response.text()}")
                        return f"📛 Request failed with status code {response.status}."
        except Exception as e:
            logging.error(f"An error occurred during the request: {str(e)}")
            if attempt < max_retries:
                logging.warning(f"Retrying after error... Attempt {attempt} of {max_retries}")
                await asyncio.sleep(retry_delay)
            else:
                logging.error("Max retries reached after exception.")
                return "📛 Request failed after maximum retries due to an exception."

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
