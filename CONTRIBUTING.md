# Contributing to PromptWatch

Thanks for helping make AI behavior easier to test.

## Local Setup

```bash
python -m pip install -e ".[dev]"
pytest
```

## Good First Issues

- Add a new deterministic rule in `src/promptwatch/rules.py`
- Add examples for a common AI app pattern
- Improve CLI output while keeping JSON output stable
- Add docs for CI usage in real repositories

## Design Principles

- Keep the core deterministic by default.
- Make provider-specific behavior optional.
- Prefer small test files that teams can review in pull requests.
- Keep reports useful for both engineers and product reviewers.

## Pull Request Checklist

- Tests cover the changed behavior.
- New user-facing behavior is documented in `README.md` or `docs/`.
- CLI exit codes remain CI-friendly.

