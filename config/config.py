import os

class Config:
    log_level: str = "INFO"
    tg_id: str = '1'
    tg_hash: str = 'b6b154c3707471f5339bd661645ed3d6'
    tg_token: str = 'None'
    db_path: str = 'data.db'
    api_ip: str = '127.0.0.1'
    api_port: str = '1337'
    gpt_model: str = 'gpt-4o-mini'
    gpt_provider: str = 'DDG'
    gpt_tokens: int = 1024
    gpt_temperature: float = 0.7
    chat_msg_storage: int = 10
    genai_api: list = []

    @classmethod
    def load_from_env(cls):
        for key in cls.__annotations__:
            env_value = os.getenv(key.upper())
            if env_value is not None:
                current_value = getattr(cls, key)
                if isinstance(current_value, int):
                    setattr(cls, key, int(env_value))
                elif isinstance(current_value, float):
                    setattr(cls, key, float(env_value))
                elif isinstance(current_value, list):
                    setattr(cls, key, env_value.split(","))
                else:
                    setattr(cls, key, env_value)

Config.load_from_env()

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
