import json
import os

CONFIG_FILE = os.path.expanduser("~/.promptwatch_config.json")

DEFAULT_CONFIG = {
    "openai_api_key": "",
    "groq_api_key": "",
    "openrouter_api_key": ""
}

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

def set_openai_api_key(key: str) -> None:
    config = load_config()
    config["openai_api_key"] = key.strip().strip('"').strip("'").strip()
    save_config(config)

def set_groq_api_key(key: str) -> None:
    config = load_config()
    config["groq_api_key"] = key.strip().strip('"').strip("'").strip()
    save_config(config)

def set_openrouter_api_key(key: str) -> None:
    config = load_config()
    config["openrouter_api_key"] = key.strip().strip('"').strip("'").strip()
    save_config(config)
