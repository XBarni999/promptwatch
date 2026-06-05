from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TestCase:
    id: str
    input: str
    expected: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Suite:
    name: str
    cases: list[TestCase]


@dataclass(frozen=True)
class Answer:
    case_id: str
    output: str
    citations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    message: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    checks: list[CheckResult]

