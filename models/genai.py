import aiohttp, asyncio
from config.config import Config
from config import logging_config
logging = logging_config.setup_logging(__name__)

prompt = ""

async def gpt_request(text, username, history, systemprompt):
    logging.debug(f"GPT Request: {text}")
    logging.debug(f"GPT Chat History: {history}")

    model_name = Config.gpt_model

    with open('config/prompt.txt', 'r', encoding='utf-8') as file:
        txt_prompt = file.read()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={Config.genai_api}"
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

    safety_settings = []
    for safety_setting in ["HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HATE_SPEECH",
                           "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_DANGEROUS_CONTENT",
                           "HARM_CATEGORY_CIVIC_INTEGRITY"]:
        if "2.0" in model_name and "flash" in model_name:
            threshold = "OFF"
        else:
            threshold = "BLOCK_NONE"

        safety_settings.append({
            "category": safety_setting,
            "threshold": threshold
        })

    payload = {
        "system_instruction": { "parts": { "text": f"{txt_prompt}\n{systemprompt}"}},

        "safetySettings": safety_settings,

        "contents": messages,
        "generationConfig": {
            "temperature": Config.gpt_temperature,
            "maxOutputTokens": Config.gpt_tokens,
            "topP": 0.95,
            "topK": 40,
        },
    }

    max_retries = 15
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
