import aiohttp, asyncio
from config.config import Config
from config import logging_config
logging = logging_config.setup_logging(__name__)

prompt = ""

async def gpt_request(text, username, history, systemprompt):
    logging.debug(f"GPT Request: {text}")
    logging.debug(f"GPT Chat History: {history}")
    with open('config/prompt.txt', 'r', encoding='utf-8') as file:
        txt_prompt = file.read()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{Config.genai_model}:generateContent?key={Config.genai_api}"
    headers = {
        "Content-Type": "application/json"
    }
    messages = []
    logging.debug(f"GPT Prompt: {systemprompt}")
    for user_text, message_text in history:
        if user_text == 'bot':
            messages.append({
                "role": "model",
                "parts": [{"text": message_text}]
            })
        else:
            messages.append({
                "role": "user",
                "parts": [{"text": f"{user_text}: {message_text}"}]
            })

    messages.append({
        "role": "user",
        "parts": [{"text": f"{username}: {text}"}]
    })

    logging.debug(f"Messages tuples: {messages}")

    payload = {
        "system_instruction": { "parts": { "text": f"{txt_prompt}\n{systemprompt}"}},

        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"}
        ],

        "contents": messages,
        "generationConfig": {
            "temperature": Config.gpt_temperature,
            "maxOutputTokens": Config.gpt_tokens,
            "topP": 0.95,
            "topK": 40,
        },
    }

    max_retries = 3
    retry_delay = 15  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["candidates"][0]["content"]["parts"][0]["text"]
                        logging.debug(f"GPT Response: {content}")
                        return content
                    elif response.status == 500:
                        logging.warning(f"Attempt {attempt} failed with status code 500. Retrying in {retry_delay} seconds...")
                        if attempt < max_retries:
                            await asyncio.sleep(retry_delay)
                        else:
                            logging.error("Max retries reached. Request failed.")
                            return "Request failed after maximum retries with status code 500"
                    else:
                        logging.error(f"Request failed with status code {response.status}\n{await response.text()}")
                        return f"Request failed with status code {response.status}"
        except Exception as e:
            logging.error(f"An error occurred during the request: {str(e)}")
            if attempt < max_retries:
                logging.warning(f"Retrying after error... Attempt {attempt} of {max_retries}")
                await asyncio.sleep(retry_delay)
            else:
                logging.error("Max retries reached after exception.")
                return "Request failed after maximum retries due to an exception"

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
