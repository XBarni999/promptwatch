from promptwatch.models import Answer
from promptwatch.rules import run_checks, _must_include, _must_not_include, _regex, _json_valid, _citations

def test_must_include():
    results = _must_include("Hello World", ["hello", "WORLD", "missing"])
    assert results[0].passed
    assert results[1].passed
    assert not results[2].passed
    assert results[0].name == "must_include"

def test_must_not_include():
    results = _must_not_include("Hello World", ["hello", "WORLD", "missing"])
    assert not results[0].passed
    assert not results[1].passed
    assert results[2].passed
    assert results[0].name == "must_not_include"

def test_regex():
    results = _regex("order #12345", ["[a-z]+ #[0-9]+", "missing"])
    assert results[0].passed
    assert not results[1].passed
    assert results[0].name == "regex"

def test_json_valid():
    # Test valid JSON
    assert _json_valid('{"key": "value"}', True)[0].passed
    assert _json_valid('{"key": "value"}', {"required": True})[0].passed
    # Test invalid JSON
    assert not _json_valid("invalid json", True)[0].passed
    # Test not required
    assert _json_valid("invalid json", False) == []
    assert _json_valid("invalid json", {"required": False}) == []
    # Test config None
    assert _json_valid("invalid json", None) == []

def test_citations():
    answer = Answer(case_id="case", output="text", citations=["cite1", "cite2"])
    # Satisfies minimum
    assert _citations(answer, {"min_count": 1})[0].passed
    assert _citations(answer, {"min_count": 2})[0].passed
    # Does not satisfy minimum
    assert not _citations(answer, {"min_count": 3})[0].passed
    # No config
    assert _citations(answer, None) == []

def test_run_checks_none_answer():
    results = run_checks({"must_include": ["hello"]}, None)
    assert len(results) == 1
    assert not results[0].passed
    assert results[0].name == "answer_present"

def test_run_checks_empty_expected_has_output():
    results = run_checks({}, Answer(case_id="case", output="some text"))
    assert len(results) == 1
    assert results[0].passed
    assert results[0].name == "has_output"

    # Empty output
    results_empty = run_checks({}, Answer(case_id="case", output="   "))
    assert len(results_empty) == 1
    assert not results_empty[0].passed
    assert results_empty[0].name == "has_output"
