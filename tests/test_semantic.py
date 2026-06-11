import json
from unittest.mock import patch, MagicMock
from promptwatch.models import Answer
from promptwatch.rules import run_checks
from promptwatch.adapters import AdapterResponse

class MockJudge:
    def __init__(self, output_json_str):
        self.output_json_str = output_json_str
        self.last_case = None

    def generate(self, case):
        self.last_case = case
        return AdapterResponse(output=self.output_json_str)


def test_semantic_rule_passed():
    # Setup mock judge that returns a passed evaluation
    judge = MockJudge(json.dumps({"passed": True, "reason": "Output is indeed polite."}))
    
    checks = run_checks(
        {"semantic": ["must be polite"]},
        Answer("case_1", "Hello, thank you for contacting support."),
        case_input="User message",
        judge=judge
    )
    
    assert len(checks) == 1
    assert checks[0].passed
    assert checks[0].name == "semantic"
    assert "Output is indeed polite" in checks[0].message
    assert "must be polite" in judge.last_case.input


def test_semantic_rule_failed():
    # Setup mock judge that returns a failed evaluation
    judge = MockJudge(json.dumps({"passed": False, "reason": "Contains a prescription dose."}))
    
    checks = run_checks(
        {"semantic": "should avoid medication dosing"},
        Answer("case_2", "Please take 50mg of Aspirin."),
        case_input="What dose should I take?",
        judge=judge
    )
    
    assert len(checks) == 1
    assert not checks[0].passed
    assert "Contains a prescription dose" in checks[0].message
