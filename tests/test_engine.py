from promptwatch.engine import evaluate_suite
from promptwatch.models import Answer, Suite, TestCase

def test_evaluate_suite_passes_all_checks():
    suite = Suite(
        name="demo",
        cases=[
            TestCase(
                id="case-1",
                input="Question",
                expected={
                    "must_include": ["30 days"],
                    "must_not_include": ["always"],
                    "citations": {"min_count": 1},
                },
            )
        ],
    )
    answers = {
        "case-1": Answer(
            case_id="case-1",
            output="Refunds are available for 30 days.",
            citations=["policy.md"],
        )
    }

    report = evaluate_suite(suite, answers)

    assert report.ok
    assert report.passed == 1
    assert report.failed == 0

def test_evaluate_suite_reports_missing_answer():
    suite = Suite(name="demo", cases=[TestCase(id="missing", input="Question")])

    report = evaluate_suite(suite, {})

    assert not report.ok
    assert report.failed == 1
    assert report.cases[0].checks[0].name == "answer_present"

def test_evaluate_suite_mixed_results():
    suite = Suite(
        name="demo",
        cases=[
            TestCase(id="case-pass", input="Q1", expected={"must_include": ["yes"]}),
            TestCase(id="case-fail", input="Q2", expected={"must_include": ["no"]}),
        ],
    )
    answers = {
        "case-pass": Answer(case_id="case-pass", output="yes it is"),
        "case-fail": Answer(case_id="case-fail", output="yes it is"),  # fails 'no'
    }

    report = evaluate_suite(suite, answers)
    assert not report.ok
    assert report.passed == 1
    assert report.failed == 1

def test_evaluate_suite_empty():
    suite = Suite(name="empty", cases=[])
    report = evaluate_suite(suite, {})
    assert report.ok
    assert report.passed == 0
    assert report.failed == 0
