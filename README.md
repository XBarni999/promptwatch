# PromptWatch

Model-agnostic regression tests for prompts, agents, and RAG pipelines.

PromptWatch helps AI teams catch behavior drift before it reaches users. Write small YAML test suites, run them against saved outputs or live adapters, and get a clear pass/fail report for correctness, safety, refusal behavior, citations, tone, and custom rules.

## Why

AI features change even when your app code does not. A new model version, prompt edit, retrieval tweak, or tool schema change can quietly break important behavior. PromptWatch gives open-source projects and small teams a lightweight way to test LLM behavior in CI.

## Features

- YAML test suites for prompts, agents, chatbots, and RAG answers
- Offline mode for testing stored model outputs
- Rule checks for required text, forbidden text, regexes, semantic labels, citations, and JSON validity
- Simple CLI with machine-readable JSON reports
- Provider-agnostic adapter interface
- GitHub Actions friendly exit codes

## Install

```bash
git clone https://github.com/your-org/promptwatch.git
cd promptwatch
python -m pip install -e ".[dev]"
```

## Quick Start

```bash
promptwatch run examples/rag_support.yaml --answers examples/answers.json
```

Expected output:

```text
PromptWatch: 3 passed, 0 failed
```

## Example Suite

```yaml
name: RAG support assistant
cases:
  - id: refund-policy-citation
    input: "Can I get a refund after 40 days?"
    expected:
      must_include:
        - "30 days"
      must_not_include:
        - "always"
      citations:
        min_count: 1
```

## CI Usage

```yaml
- name: Run AI regression suite
  run: promptwatch run examples/rag_support.yaml --answers examples/answers.json
```

PromptWatch exits with code `1` when any case fails, so it can block a pull request before a prompt or retrieval change ships.

## What To Test

- RAG answers cite the right source and do not invent policy details
- Safety-critical prompts refuse unsafe requests without becoming unhelpful
- Tool-calling outputs remain valid JSON
- Agent responses preserve product tone and required disclaimers
- Model migrations do not lose key behavior

## Project Status

PromptWatch is intentionally small. The first goal is to make AI regression testing easy enough that people actually keep it in CI.

## Roadmap

- Live adapters for OpenAI-compatible APIs, local models, and custom HTTP endpoints
- Snapshot comparison between two model runs
- Built-in semantic checks using pluggable judge models
- HTML reports for product and QA teams
- Dataset importers from production feedback and support tickets

## Contributing

Issues and pull requests are welcome. Good first contributions include new rule types, adapter examples, documentation improvements, and real-world test suite examples with private data removed.

## License

MIT
