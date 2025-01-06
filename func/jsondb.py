import json
from config.config import Config

def load_database():
    try:
        with open(Config.db_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_database(database):
    with open(Config.db_file, "w") as file:
        json.dump(database, file, indent=4)

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
