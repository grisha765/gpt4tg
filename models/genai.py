import aiohttp, asyncio, base64, os, magic, random
from config.config import Config
from config import logging_config
logging = logging_config.setup_logging(__name__)

prompt = ""

current_key = {"number": 0}

async def gpt_request(text, username, history, systemprompt, media_file=False):
    logging.debug(f"GPT Request: {text}")
    logging.debug(f"GPT Chat History: {history}")

    model_name = Config.gpt_model
    api_keys = Config.genai_api

    with open('config/prompt.txt', 'r', encoding='utf-8') as file:
        txt_prompt = file.read()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_keys[current_key["number"]].strip()}"
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
    if media_file:
        text = text.split("text:")[-1].strip()
        mime = magic.Magic(mime=True)
        if os.path.isfile(media_file):
            mime_type = mime.from_file(media_file)
            with open(media_file, "rb") as img_file:
                encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
            messages.append({
                "role": "user",
                "parts": [
                    {"text": f"{username}: {text}"},
                    {"inline_data": {"mime_type": mime_type, "data": encoded_image}}
                          ]
            })
        else:
            messages.append({
                "role": "user",
                "parts": [{"text": f"{username}: {text}"}]
            })
            logging.debug(f"Messages tuples: {messages}")
    else:
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

    if "2.0" in model_name:
        search = [{
            "googleSearch": {}
        }]
    else:
        search = [{
            "googleSearchRetrieval": {
                "dynamic_retrieval_config": {
                    "mode": "MODE_DYNAMIC",
                    "dynamic_threshold": 0.3,
                }
            }
        }]

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
        "tools": search
    }

    max_retries = 15

    for attempt in range(1, max_retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content_parts = data["candidates"][0]["content"]["parts"]
                        content = "".join(part["text"] for part in content_parts)
                        logging.debug(f"GPT Response: {content}")
                        return content
                    elif response.status == 429:
                        logging.warning(f"Request failed with status code {response.status} when using index: {current_key["number"]}. Updating index attempt {attempt} of {max_retries}...")
                        if attempt < max_retries:
                            new_index = random.choice([i for i in range(len(api_keys)) if i != current_key["number"]])
                            current_key["number"] = new_index
                        else:
                            return f"📛 Request failed with status code {response.status}."
                    else:
                        logging.error(f"Request failed with status code {response.status}\n{await response.text()}")
                        return f"📛 Request failed with status code {response.status}."
        except Exception as e:
            logging.error(f"An error occurred during the request: {str(e)}")
            return f"📛 An error occurred during the request: {str(e)}"

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
