from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from typing import Any

from .models import Answer, CheckResult


def run_checks(expected: dict[str, Any], answer: Answer | None, case_input: str = "", judge: Any = None) -> list[CheckResult]:
    if answer is None:
        return [CheckResult("answer_present", False, "No answer was provided for this case.")]

    checks: list[CheckResult] = []
    output = answer.output

    checks.extend(_must_include(output, expected.get("must_include", [])))
    checks.extend(_must_not_include(output, expected.get("must_not_include", [])))
    checks.extend(_regex(output, expected.get("regex", [])))
    checks.extend(_json_valid(output, expected.get("json")))
    checks.extend(_citations(answer, expected.get("citations")))
    checks.extend(_semantic(output, case_input, expected.get("semantic", []), judge))

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


def _semantic(output: str, case_input: str, criteria: Any, judge: Any) -> list[CheckResult]:
    if not criteria:
        return []
    
    if isinstance(criteria, str):
        criteria = [criteria]
        
    if not isinstance(criteria, Iterable):
        return []
        
    results = []
    
    if judge is None:
        from .adapters import OpenAIAdapter, GroqAdapter, OpenRouterAdapter
        if os.environ.get("OPENAI_API_KEY"):
            judge = OpenAIAdapter()
        elif os.environ.get("GROQ_API_KEY"):
            judge = GroqAdapter()
        elif os.environ.get("OPENROUTER_API_KEY"):
            judge = OpenRouterAdapter()
            
    if judge is None:
        for criterion in criteria:
            results.append(
                CheckResult(
                    "semantic",
                    False,
                    f"Semantic check skipped: No LLM judge adapter was provided, and no cloud API key environment variable (OPENAI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY) was found."
                )
            )
        return results

    for criterion in criteria:
        prompt = f"""You are an objective AI judge evaluating the output of an AI system against a semantic criterion.

Test Case Input:
"{case_input}"

AI Output to Evaluate:
"{output}"

Criterion to check:
"{criterion}"

Does the AI Output satisfy the Criterion?
Respond in valid JSON format with the following keys:
- "passed": true/false
- "reason": A short explanation of why the output did or did not pass the criterion.
"""
        from .models import TestCase as JudgeTestCase
        judge_case = JudgeTestCase(id=f"judge-{criterion[:10]}", input=prompt)
        try:
            response = judge.generate(judge_case)
            res_content = response.output.strip()
            if res_content.startswith("```"):
                lines = res_content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                res_content = "\n".join(lines).strip()
            
            res_json = json.loads(res_content)
            passed = bool(res_json.get("passed"))
            reason = str(res_json.get("reason", f"Criterion evaluation finished. Result: {passed}"))
            results.append(
                CheckResult(
                    "semantic",
                    passed,
                    f"Criterion: '{criterion}'. Details: {reason}"
                )
            )
        except Exception as e:
            results.append(
                CheckResult(
                    "semantic",
                    False,
                    f"Semantic evaluation failed for criterion '{criterion}': {e}"
                )
            )
            
    return results

