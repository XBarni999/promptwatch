from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import Answer, CaseResult, Suite
from .rules import run_checks


@dataclass(frozen=True)
class EvaluationReport:
    suite_name: str
    total: int
    passed: int
    failed: int
    cases: list[CaseResult]

    @property
    def ok(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_suite(suite: Suite, answers: dict[str, Answer]) -> EvaluationReport:
    case_results: list[CaseResult] = []
    for case in suite.cases:
        checks = run_checks(case.expected, answers.get(case.id))
        passed = all(check.passed for check in checks)
        case_results.append(CaseResult(case_id=case.id, passed=passed, checks=checks))

    passed_count = sum(1 for result in case_results if result.passed)
    failed_count = len(case_results) - passed_count
    return EvaluationReport(
        suite_name=suite.name,
        total=len(case_results),
        passed=passed_count,
        failed=failed_count,
        cases=case_results,
    )

