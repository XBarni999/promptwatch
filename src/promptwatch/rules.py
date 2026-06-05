from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

from .models import Answer, CheckResult


def run_checks(expected: dict[str, Any], answer: Answer | None) -> list[CheckResult]:
    if answer is None:
        return [CheckResult("answer_present", False, "No answer was provided for this case.")]

    checks: list[CheckResult] = []
    output = answer.output

    checks.extend(_must_include(output, expected.get("must_include", [])))
    checks.extend(_must_not_include(output, expected.get("must_not_include", [])))
    checks.extend(_regex(output, expected.get("regex", [])))
    checks.extend(_json_valid(output, expected.get("json")))
    checks.extend(_citations(answer, expected.get("citations")))

    if not checks:
        checks.append(CheckResult("has_output", bool(output.strip()), "Answer output is present."))

    return checks


def _must_include(output: str, phrases: Iterable[str]) -> list[CheckResult]:
    results = []
    folded = output.casefold()
    for phrase in phrases:
        passed = str(phrase).casefold() in folded
        results.append(
            CheckResult(
                "must_include",
                passed,
                f'Expected output to include "{phrase}".',
            )
        )
    return results


def _must_not_include(output: str, phrases: Iterable[str]) -> list[CheckResult]:
    results = []
    folded = output.casefold()
    for phrase in phrases:
        passed = str(phrase).casefold() not in folded
        results.append(
            CheckResult(
                "must_not_include",
                passed,
                f'Expected output to avoid "{phrase}".',
            )
        )
    return results


def _regex(output: str, patterns: Iterable[str]) -> list[CheckResult]:
    results = []
    for pattern in patterns:
        passed = re.search(str(pattern), output, flags=re.IGNORECASE | re.MULTILINE) is not None
        results.append(CheckResult("regex", passed, f"Expected output to match /{pattern}/."))
    return results


def _json_valid(output: str, config: Any) -> list[CheckResult]:
    if config is None:
        return []
    required = bool(config) if isinstance(config, bool) else bool(config.get("required", True))
    if not required:
        return []
    try:
        json.loads(output)
    except json.JSONDecodeError as exc:
        return [CheckResult("json_valid", False, f"Output is not valid JSON: {exc.msg}.")]
    return [CheckResult("json_valid", True, "Output is valid JSON.")]


def _citations(answer: Answer, config: Any) -> list[CheckResult]:
    if not config:
        return []
    min_count = int(config.get("min_count", 0))
    passed = len(answer.citations) >= min_count
    return [
        CheckResult(
            "citations",
            passed,
            f"Expected at least {min_count} citation(s), found {len(answer.citations)}.",
        )
    ]

