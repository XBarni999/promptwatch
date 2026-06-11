import json
import pytest
from unittest.mock import patch
from promptwatch import config

def test_load_config_default(tmp_path):
    temp_config_file = str(tmp_path / "config.json")
    with patch("promptwatch.config.CONFIG_FILE", temp_config_file):
        cfg = config.load_config()
        assert cfg == config.DEFAULT_CONFIG

def test_save_and_load_config(tmp_path):
    temp_config_file = str(tmp_path / "config.json")
    with patch("promptwatch.config.CONFIG_FILE", temp_config_file):
        # Update OpenAI key
        config.set_openai_api_key("sk-testopenai")
        cfg = config.load_config()
        assert cfg["openai_api_key"] == "sk-testopenai"
        assert cfg["groq_api_key"] == ""

        # Update Groq key with quotes
        config.set_groq_api_key("'gsk-testgroq'")
        cfg = config.load_config()
        assert cfg["groq_api_key"] == "gsk-testgroq"

        # Update OpenRouter key
        config.set_openrouter_api_key('"sk-or-test"')
        cfg = config.load_config()
        assert cfg["openrouter_api_key"] == "sk-or-test"

def test_load_config_corrupted(tmp_path):
    temp_config_file = tmp_path / "config.json"
    temp_config_file.write_text("invalid json format", encoding="utf-8")
    with patch("promptwatch.config.CONFIG_FILE", str(temp_config_file)):
        cfg = config.load_config()
        assert cfg == config.DEFAULT_CONFIG
