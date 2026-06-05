from promptwatch.loaders import _parse_simple_yaml


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

