# gpt4tg
A Telegram bot that integrates GPT-powered conversations with activation-based functionality for group chats.

### Initial Setup

1. **Clone the repository**: Clone this repository using `git clone`.
2. **Download Dependencies**: Download the required dependencies into the Virtual Environment `venv` using `uv`.

```shell
git clone https://github.com/grisha765/gpt4tg.git
cd gpt4tg
uv sync
```

### Deploy

- Run the bot:
    ```bash
    TG_TOKEN="your_telegram_bot_token" uv run main.py
    ```

- Other working env's:
    ```env
    LOG_LEVEL="INFO"
    TG_ID="your_telegram_api_id"
    TG_HASH="your_telegram_api_hash"
    TG_TOKEN="your_telegram_bot_token"
    DB_PATH="data.db"
    API_IP="127.0.0.1"
    API_PORT="1337"
    GENAI_API="your_gemini_api_key, your_gemini_api_key2, your_gemini_api_key3" # if not empty then gemini is activated
    GPT_MODEL="gpt-4o-mini" # also set for gemini
    GPT_PROVIDER="DDG" # only works in gpt4free or ollama
    GPT_TOKENS="512"
    GPT_TEMPERATURE="0.5"
    CHAT_MSG_STORAGE="10"
    ```

#### Container

- Pull container:
    ```bash
    podman pull ghcr.io/grisha765/gpt4tg:latest
    ```

- Run bot:
    ```bash
    mkdir -p $HOME/database/ && \
    podman run --tmpfs /tmp -d \
    --name gpt4tg \
    -v $HOME/database:/app/database:z \
    -e TG_TOKEN="your_telegram_bot_token" \
    ghcr.io/grisha765/gpt4tg:latest
    ```

## Usage

### Bot Commands

- **Activation**:
    - Add the bot to a `group chat`.
    - The bot will generate a `password` in the `logs`.
    - `Activate` the group with the command:
      ```
      /activate <password>
      ```

- **GPT Requests**:
    - Direct request `create virtual chat`:
      ```
      /gpt <message>
      ```
    - Reply-based request:
      Reply to the message generated by the bot to continue the `conversation` in this chat.

## Features

- Handles group chat `activations` with a `password` system.
- Supports `OpenAI API` and `Gemini API` responses for user queries.
- `Queue-based` message handling to process requests efficiently.
- Chat history maintained for context in `conversations`.
- `Configurable` through environment variables.
