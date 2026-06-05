from __future__ import annotations

import argparse
import json
import sys

from .engine import evaluate_suite
from .loaders import load_answers, load_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="promptwatch",
        description="Run regression checks for prompts, agents, and RAG pipelines.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a PromptWatch suite.")
    run_parser.add_argument("suite", help="Path to a YAML or JSON suite file.")
    run_parser.add_argument("--answers", required=True, help="Path to answers JSON.")
    run_parser.add_argument("--json", action="store_true", help="Print a JSON report.")

    args = parser.parse_args(argv)
    if args.command == "run":
        report = evaluate_suite(load_suite(args.suite), load_answers(args.answers))
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(f"PromptWatch: {report.passed} passed, {report.failed} failed")
            for case in report.cases:
                marker = "PASS" if case.passed else "FAIL"
                print(f"{marker} {case.case_id}")
                for check in case.checks:
                    if not check.passed:
                        print(f"  - {check.message}")
        return 0 if report.ok else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())

