# gpt4tg
This project is a Telegram bot for interactive conversations with advanced language models (OpenAI, Gemini, etc). The bot can be added to Telegram groups and supports chat-based communication, group activation, and custom usernames for users. It supports LLM session management and group-specific permissions.

### Initial Setup

1. **Clone the repository**: Clone this repository using `git clone`.
2. **Create Virtual Env**: Create a Python Virtual Environment `venv` to download the required dependencies and libraries.
3. **Download Dependencies**: Download the required dependencies into the Virtual Environment `venv` using `uv`.

```shell
git clone https://github.com/grisha765/gpt4tg.git
cd gpt4tg
python -m venv .venv
.venv/bin/python -m pip install uv
.venv/bin/python -m uv sync
```

## Usage

### Deploy

- Run the bot:
    ```bash
    TG_TOKEN="telegram_bot_token" .venv/bin/python bot
    ```

### Container

- Pull the container:
    ```bash
    podman pull ghcr.io/grisha765/gpt4tg:latest
    ```

- Deploy using Podman:
    ```bash
    mkdir -p $HOME/database/ && \
    podman run -d \
    --name gpt4tg \
    -v $HOME/database:/app/database:z \
    -e TG_TOKEN="your_telegram_bot_token" \
    ghcr.io/grisha765/gpt4tg:latest
    ```

## Environment Variables

The following environment variables control the startup of the project:

| Variable          | Values                              | Description                                                        |
| ----------------- | ----------------------------------- | ------------------------------------------------------------------ |
| `LOG_LEVEL`       | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Logging verbosity                                                  |
| `TG_ID`           | *integer*                           | Telegram API ID from [my.telegram.org](https://my.telegram.org)    |
| `TG_HASH`         | *string*                            | Telegram API hash                                                  |
| `TG_TOKEN`        | *string*                            | Bot token issued by [@BotFather](https://t.me/BotFather)           |
| `DB_PATH`         | *string*                            | Path to SQLite database file (default `data.db`)                   |
| `MODEL_NAME`      | *string*                            | Name of the LLM model to use (`gpt-3.5-turbo`, `gemini-2.0-flash`) |
| `API_KEY`         | *comma-separated*                   | API keys for the LLM providers                                     |
| `OPENAI_BASE_URL` | *string*                            | Custom OpenAI API base URL (optional)                              |

## Basic Bot Commands

- `/gpt <your_message>` — Start a conversation with the bot.
- `/gpt {system prompt} <your_message>` — Set a custom prompt for this conversation.
- `/gpt !setname <username>` — Set or change your chat username.
- `/gpt !setname reset` — Reset your custom username.
    - The bot requires activation in each group before use. The activation password is generated and logged when the bot joins a group. Use `/activate <password>` to enable the bot.

## Features

- **AI-powered Conversations**:
  Users can interact with advanced language models directly in Telegram groups.
- **Group Activation System**:
  Bot can be enabled/disabled in each group via activation password (for privacy and moderation).
- **Username Management**:
  Users can set custom usernames or reset them with chat commands.
- **Multi-Provider Support**:
  Works with both OpenAI and Gemini (Google) APIs, supports multiple API keys and fallback logic.
- **Session Management**:
  Each message chain maintains its own chat session context for relevant replies.
