from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .models import Answer, TestCase


@dataclass(frozen=True)
class AdapterResponse:
    output: str
    citations: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class ModelAdapter(Protocol):
    """Protocol for live model or application adapters."""

    def generate(self, case: TestCase) -> AdapterResponse:
        """Return the model output for one test case."""


def answer_from_response(case: TestCase, response: AdapterResponse) -> Answer:
    return Answer(
        case_id=case.id,
        output=response.output,
        citations=response.citations,
        metadata=response.metadata,
    )

