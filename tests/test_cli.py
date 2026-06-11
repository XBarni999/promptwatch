import pytest
from unittest.mock import patch
from promptwatch.cli import prompt_input, MainMenuRedirect, ExitCLI, run_interactive_menu

def test_prompt_input_standard():
    with patch("builtins.input", return_value="hello"):
        assert prompt_input("prompt: ") == "hello"

def test_prompt_input_default():
    with patch("builtins.input", return_value=""):
        assert prompt_input("prompt: ", default="my_default") == "my_default"

@pytest.mark.parametrize("quit_val", ["0", "q", "back", "exit", " Q ", "Back"])
def test_prompt_input_redirect(quit_val):
    with patch("builtins.input", return_value=quit_val):
        with pytest.raises(MainMenuRedirect):
            prompt_input("prompt: ")

@pytest.mark.parametrize("quit_val", ["0", "q", "back", "exit"])
def test_prompt_input_no_redirect_when_disallowed(quit_val):
    with patch("builtins.input", return_value=quit_val):
        assert prompt_input("prompt: ", allow_back=False) == quit_val

def test_prompt_input_exit_on_keyboard_interrupt():
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        with pytest.raises(ExitCLI):
            prompt_input("prompt: ")

def test_prompt_input_exit_on_eof_error():
    with patch("builtins.input", side_effect=EOFError):
        with pytest.raises(ExitCLI):
            prompt_input("prompt: ")

def test_run_interactive_menu_exit_immediately():
    # Choice 4 exits
    with patch("builtins.input", return_value="4"):
        assert run_interactive_menu() == 0

def test_run_interactive_menu_redirect_flow():
    # We choose "1" (Run suite) -> suite path prompt: user types "0" (to go back to main menu) -> choice: user types "4" (to exit)
    inputs = ["1", "0", "4"]
    with patch("builtins.input", side_effect=inputs):
        assert run_interactive_menu() == 0

def test_main_setup_keys(tmp_path):
    from promptwatch.cli import main
    temp_config_file = str(tmp_path / "config.json")
    with patch("promptwatch.config.CONFIG_FILE", temp_config_file):
        assert main(["--setup-openai", "key-openai"]) == 0
        assert main(["--setup-groq", "key-groq"]) == 0
        assert main(["--setup-openrouter", "key-openrouter"]) == 0
        assert main(["--setup-openai", ""]) == 0
