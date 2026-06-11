# PromptWatch 🔍

[![CI](https://github.com/XBarni999/promptwatch/actions/workflows/ci.yml/badge.svg)](https://github.com/XBarni999/promptwatch/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

**PromptWatch** is a model-agnostic, lightweight CLI tool designed for testing LLM responses, agent actions, and RAG pipelines. It functions like regression tests for AI behavior, ensuring that changes to your prompts, retrieval logic, or model endpoints don't silently degrade your system.

---

## 🌟 Key Features

- **Live Adapters (Cloud API)**: Query live models directly (OpenAI, Groq, OpenRouter) or run evaluations against custom HTTP endpoints (e.g. your own RAG server) on the fly.
- **Semantic LLM-Judge Checks**: Verify soft/behavioral criteria (e.g., tone, refusal policy, safety limits) using an LLM as a judge.
- **Stunning HTML Reports**: Generate beautiful, interactive visual reports with status stats, filters, searching, and expandable cards detailing input, output, and evaluation checks.
- **Snapshot Comparison (Diffs)**: Contrast the outputs of two separate runs (e.g. before/after prompt changes) side-by-side in HTML with word-level highlight diffs.
- **CI/CD Integration**: Returns standard exit codes (`0` for pass, `1` for fail) to easily block bad pull requests in GitHub Actions.

---

## 🚀 Installation

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/XBarni999/promptwatch.git
cd promptwatch
python -m pip install -e ".[dev]"
```

---

## 📖 Available CLI Subcommands

### 1. `run` (Execute Suites)
Evaluate test cases using loaded answers or by querying live endpoints.

```bash
# Options list:
#   suite                 Path to a YAML or JSON suite file.
#   -a, --answers         Path to answers JSON file (Offline Mode).
#   -j, --json            Print report output in JSON format.
#   --html <path>         Path to generate a beautiful interactive HTML dashboard.
#   -ad, --adapter        Live model adapter: openai, openrouter, groq, http.
#   -m, --model           Model name (e.g., gpt-4o-mini).
#   -u, --url             HTTP endpoint URL (required for 'http' adapter).
#   --json-path           Dot-path to extract outputs from HTTP response.
#   -s, --save-answers    Path to save the generated answers JSON file.
#   --ja                  Judge adapter for semantic rules (openai, openrouter, groq).
#   --jm                  Model name for the judge.
```

### 2. `compare` (Run Differences)
Find differences in outputs between two evaluation snapshots.

```bash
promptwatch compare old_answers.json new_answers.json --html diff.html
```

---

## 📚 Step-by-Step Tutorial

### Step 1: Create a Test Suite
Create a file named `my_suite.yaml`:

```yaml
name: Help Desk Assistant
cases:
  - id: refund-policy
    input: "Can I get a refund for my order after 45 days?"
    expected:
      must_include:
        - "30 days"
      must_not_include:
        - "always"
      semantic:
        - "The AI must politely decline the refund."
```

### Step 2: Run a Live Evaluation (Cloud API)
We'll query a live model (e.g., OpenAI or Groq) to test the prompt behavior. Set your API key in the terminal first:

**On Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=your_openai_key_here
```
**On Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your_openai_key_here"
```
**On Bash:**
```bash
export OPENAI_API_KEY="your_openai_key_here"
```

Now, run the suite live, save the outputs to `run_a.json`, and output a premium visual HTML dashboard to `report.html`:

```bash
promptwatch run my_suite.yaml -ad openai -m gpt-4o-mini -s run_a.json --html report.html
```

You can open `report.html` in any browser to inspect the visual breakdown.

### Step 3: Run Offline Mode (Fast Check)
If you already have a saved answers file, you can evaluate rules offline in milliseconds without spending LLM tokens:

```bash
promptwatch run my_suite.yaml -a run_a.json
```

### Step 4: Compare Prompts (Regression Testing)
Suppose you adjust your system instructions or switch your model, and want to see how the outputs changed. 

1. Run the test suite again and save to a new snapshot:
   ```bash
   promptwatch run my_suite.yaml -ad openai -m gpt-4o -s run_b.json
   ```
2. Generate a visual side-by-side diff report:
   ```bash
   promptwatch compare run_a.json run_b.json --html compare.html
   ```

Opening `compare.html` will showcase a side-by-side comparison of the old output versus the new output, with green and red highlighting for word-level differences.

---

## 🛠 Rule Types & Syntax

### Deterministic Rules
- **`must_include`**: Verifies specified phrases appear in the output.
- **`must_not_include`**: Ensures specified phrases are absent.
- **`regex`**: Checks that the output matches regular expressions.
- **`json`**: Requires the output to parse as valid JSON.
- **`citations`**: Validates a minimum number of citation references.

Example:
```yaml
expected:
  must_include: ["Hello", "Welcome"]
  regex: ["order #[0-9]+"]
  json: true
```

### Semantic Rules (LLM Judge)
- **`semantic`**: Evaluates behavioral rules using a cloud LLM as an objective judge.

Example:
```yaml
expected:
  semantic:
    - "AI must remain friendly and supportive"
    - "AI must not recommend prescription medication"
```

---

## 🧪 Running Tests

To run the test suite and confirm everything works correctly:

```bash
python -m pytest
```

---

## 📄 License

PromptWatch is open-source software licensed under the [MIT License](LICENSE).
