# PromptWatch

[![CI](https://github.com/XBarni999/promptwatch/actions/workflows/ci.yml/badge.svg)](https://github.com/XBarni999/promptwatch/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

PromptWatch is a model-agnostic, lightweight CLI tool designed for testing LLM responses, agent actions, and RAG pipelines. It acts as a regression testing suite for AI behavior, ensuring that changes to your prompts, retrieval logic, or model endpoints do not silently degrade your system.

---

## Key Features

- **Live Adapters (Cloud API)**: Query OpenAI, Groq, and OpenRouter directly, or test custom HTTP endpoints live.
- **Local API Key Storage**: Register API keys once locally to avoid setting environment variables on every launch.
- **Semantic LLM-Judge Checks**: Verify soft criteria (such as tone, safety limits, or refusal policies) using a cloud LLM as an objective judge.
- **HTML Reports**: Generate interactive visual reports with status statistics, input/output displays, search/filters, and check details.
- **Snapshot Comparison (Diffs)**: Compare outputs from two runs side-by-side in HTML with word-level diff highlighting.
- **CI/CD Support**: Returns standard exit codes (0 for pass, 1 for fail) to block pull requests in GitHub Actions if a check fails.

---

## How to Start Using PromptWatch

Follow this simple guide to set up PromptWatch and run your first test.

### Step 1: Install PromptWatch
From the root of the cloned PromptWatch directory, run:

```bash
python -m pip install -e ".[dev]"
```

This registers the `promptwatch` command globally in your terminal.

### Step 2: Register your API Keys (Local Storage)
Instead of setting temporary environment variables every time you run a command, you can save your cloud API keys to your local configuration. Run the setup command for the API you want to use:

```bash
# Register OpenAI key
promptwatch --setup-openai "your_openai_key"

# Register Groq key
promptwatch --setup-groq "your_groq_key"

# Register OpenRouter key
promptwatch --setup-openrouter "your_openrouter_key"
```

Keys are securely saved to `~/.promptwatch_config.json` in your user directory. To clear a key, simply pass an empty string (e.g. `promptwatch --setup-openai ""`).

### Step 3: Launch the Interactive TUI Menu
If you don't want to type long commands, you can start PromptWatch in interactive mode by running the command without any subcommands:

```bash
promptwatch
```

This launches a step-by-step terminal menu guiding you through running test suites, configuring API keys, or comparing snapshots. At any submenu prompt, you can type `0`, `q`, `back`, or `exit` to return to the main menu.

### Step 4: Run your First Test
To run a test, you need a test suite file (in YAML or JSON) specifying the prompt inputs and expected rules.

Run the pre-configured RAG support example suite against the provided answers file using this command:

```bash
promptwatch run examples/rag_support.yaml --answers examples/answers.json
```

Or run it using the short flag equivalent:

```bash
promptwatch run examples/rag_support.yaml -a examples/answers.json
```

### Step 5: Run a Test with Live LLM Responses
To fetch actual AI outputs live instead of reading from a pre-saved answers file, use the `-ad` / `--adapter` flag and specify a model. 

For instance, to run a test suite using OpenAI's `gpt-4o-mini` model, run:

```bash
promptwatch run examples/rag_support.yaml -ad openai -m gpt-4o-mini
```

To run it and also save the generated responses to a JSON file for future offline checks, run:

```bash
promptwatch run examples/rag_support.yaml -ad openai -m gpt-4o-mini -s my_answers.json
```

### Step 6: Generate an HTML Test Report
To compile the test results into a dashboard with dark/light modes, list of checks, prompt inputs, and model outputs, use the `--html` flag:

```bash
promptwatch run examples/rag_support.yaml -ad openai -m gpt-4o-mini --html report.html
```

You can open `report.html` directly in any web browser.

### Step 7: Compare Two Runs Side-by-Side
If you adjust your prompt or switch models and want to see how the outputs changed, you can run a comparison between two saved answers JSON files:

```bash
promptwatch compare old_run.json new_run.json --html diff.html
```

Opening `diff.html` in your browser will display a side-by-side line comparison highlighting deleted and added words.


---

## CLI Options

### Global Options
- `--setup-openai <key>`: Save your OpenAI API key locally.
- `--setup-openrouter <key>`: Save your OpenRouter API key locally.
- `--setup-groq <key>`: Save your Groq API key locally.

### `run` Subcommand Options
- `suite`: Path to the YAML or JSON suite file.
- `-a`, `--answers`: Path to a pre-saved answers JSON file.
- `-j`, `--json`: Print the report output in raw JSON format to stdout.
- `--html <path>`: Path to write a visual HTML report.
- `-ad`, `--adapter`: Live model adapter (openai, openrouter, groq, http).
- `-m`, `--model`: Model name for the adapter (e.g. gpt-4o-mini).
- `-u`, `--url`: Custom HTTP endpoint URL (required for custom RAG HTTP adapters).
- `--json-path`: JSON dot-path to resolve output in HTTP responses.
- `-s`, `--save-answers`: File path to save the generated responses.
- `--ja`, `--judge-adapter`: Adapter to use for semantic rules (openai, openrouter, groq).
- `--jm`, `--judge-model`: Model to use for the semantic judge.

### `compare` Subcommand Options
- `old_answers`: Path to the older answers JSON file.
- `new_answers`: Path to the newer answers JSON file.
- `--html <path>`: Path to write a visual side-by-side comparison report.

---

## Rule Types & Syntax

### Deterministic Rules
- **`must_include`**: The output must contain these specific phrases.
- **`must_not_include`**: The output must not contain these specific phrases.
- **`regex`**: The output must match these regular expressions.
- **`json`**: The output must be valid, parseable JSON.
- **`citations`**: The output must contain a minimum number of citations.

Example:
```yaml
expected:
  must_include:
    - "30 days"
  regex:
    - "order #[0-9]+"
```

### Semantic Rules (LLM Judge)
- **`semantic`**: Evaluates behavioral rules using a cloud LLM as an objective judge.

Example:
```yaml
expected:
  semantic:
    - "The AI must decline to give medical advice."
    - "The response tone must remain professional."
```

---

## Running Automated Tests

To verify that the CLI, adapters, and rule checkers are operating correctly, run:

```bash
python -m pytest
```

---

## License

PromptWatch is open-source software licensed under the MIT License.
