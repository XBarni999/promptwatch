from promptwatch.models import Answer
from promptwatch.rules import run_checks


def test_json_valid_rule_fails_for_plain_text():
    checks = run_checks({"json": {"required": True}}, Answer("case", "not json"))

    assert not checks[0].passed
    assert checks[0].name == "json_valid"


def test_must_not_include_is_case_insensitive():
    checks = run_checks({"must_not_include": ["guaranteed"]}, Answer("case", "This is GUARANTEED."))

    assert not checks[0].passed

