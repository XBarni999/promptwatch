import pytest
import json
from pathlib import Path
from promptwatch.loaders import load_suite, load_answers, _parse_simple_yaml, _load_mapping

def test_simple_yaml_fallback_parses_suite_shape():
    data = _parse_simple_yaml(
        """
name: Demo suite
cases:
  - id: policy
    input: "What is the policy?"
    expected:
      must_include:
        - "30 days"
      citations:
        min_count: 1
"""
    )
    assert data["name"] == "Demo suite"
    assert data["cases"][0]["id"] == "policy"
    assert data["cases"][0]["expected"]["must_include"] == ["30 days"]
    assert data["cases"][0]["expected"]["citations"]["min_count"] == 1

def test_load_suite_json(tmp_path):
    suite_data = {
        "name": "JSON Test Suite",
        "cases": [
            {
                "id": "c1",
                "input": "input text",
                "expected": {"must_include": ["text"]}
            }
        ]
    }
    file_path = tmp_path / "suite.json"
    file_path.write_text(json.dumps(suite_data), encoding="utf-8")
    
    suite = load_suite(file_path)
    assert suite.name == "JSON Test Suite"
    assert len(suite.cases) == 1
    assert suite.cases[0].id == "c1"
    assert suite.cases[0].input == "input text"
    assert suite.cases[0].expected == {"must_include": ["text"]}

def test_load_answers_format(tmp_path):
    answers_data = {
        "answers": [
            {
                "case_id": "c1",
                "output": "rendered output",
                "citations": ["src1"],
                "metadata": {"score": 0.9}
            }
        ]
    }
    file_path = tmp_path / "answers.json"
    file_path.write_text(json.dumps(answers_data), encoding="utf-8")

    answers = load_answers(file_path)
    assert len(answers) == 1
    assert answers["c1"].case_id == "c1"
    assert answers["c1"].output == "rendered output"
    assert answers["c1"].citations == ["src1"]
    assert answers["c1"].metadata == {"score": 0.9}

def test_load_answers_plain_list_format(tmp_path):
    answers_data = [
        {
            "case_id": "c2",
            "output": "plain output"
        }
    ]
    file_path = tmp_path / "answers.json"
    file_path.write_text(json.dumps(answers_data), encoding="utf-8")

    answers = load_answers(file_path)
    assert len(answers) == 1
    assert answers["c2"].output == "plain output"

def test_load_mapping_invalid_type(tmp_path):
    file_path = tmp_path / "invalid.json"
    file_path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain a mapping"):
        _load_mapping(file_path)

def test_parse_simple_yaml_indentation_error():
    # Unexpected indentation level
    bad_yaml = """
name: Bad Indent
  cases:
    - id: 1
"""
    with pytest.raises(ValueError, match="Unexpected indentation"):
        _parse_simple_yaml(bad_yaml)

def test_parse_simple_yaml_missing_colon():
    bad_yaml = """
name bad_indent
"""
    with pytest.raises(ValueError, match="Expected key/value pair"):
        _parse_simple_yaml(bad_yaml)
