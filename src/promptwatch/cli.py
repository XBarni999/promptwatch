from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import evaluate_suite
from .loaders import load_answers, load_suite
from .adapters import get_adapter, answer_from_response
from .reporter import generate_html_report, generate_comparison_report


def color_text(text: str, color_code: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{color_code}m{text}\033[0m"
    return text


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        try:
            import os
            os.system("")
        except Exception:
            pass
    parser = argparse.ArgumentParser(
        prog="promptwatch",
        description="Run regression checks for prompts, agents, and RAG pipelines.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_parser = subparsers.add_parser("run", help="Run a PromptWatch suite.")
    run_parser.add_argument("suite", help="Path to a YAML or JSON suite file.")
    run_parser.add_argument("-a", "--answers", help="Path to answers JSON.")
    run_parser.add_argument("-j", "--json", action="store_true", help="Print a JSON report.")
    run_parser.add_argument("--html", help="Path to write a beautiful HTML report.")
    
    # Adapter parameters for live runs
    run_parser.add_argument("-ad", "--adapter", choices=["openai", "openrouter", "groq", "http"], help="Live model adapter to run test cases.")
    run_parser.add_argument("-m", "--model", help="Model name for the adapter.")
    run_parser.add_argument("-u", "--url", help="Endpoint URL for the adapter (required for HTTP).")
    run_parser.add_argument("--json-path", help="JSON dot-path to resolve output in HTTP response.")
    run_parser.add_argument("-s", "--save-answers", help="Path to save the generated answers JSON file.")
    
    # Judge parameters
    run_parser.add_argument("--ja", "--judge-adapter", choices=["openai", "openrouter", "groq"], dest="judge_adapter", help="Judge adapter to run semantic checks.")
    run_parser.add_argument("--jm", "--judge-model", dest="judge_model", help="Model name for the judge adapter.")

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two answers JSON files.")
    compare_parser.add_argument("old_answers", help="Path to the older answers JSON file.")
    compare_parser.add_argument("new_answers", help="Path to the newer answers JSON file.")
    compare_parser.add_argument("--html", help="Path to write a visual HTML comparison report.")

    args = parser.parse_args(argv)
    
    if args.command == "run":
        suite_obj = load_suite(args.suite)
        answers_dict = {}
        
        # Load answers if provided
        if args.answers:
            answers_dict = load_answers(args.answers)
        elif args.adapter:
            # Run live evaluation using specified adapter
            try:
                adapter_obj = get_adapter(args.adapter, model=args.model, url=args.url, json_path=args.json_path)
            except Exception as e:
                print(color_text(f"Error initializing adapter: {e}", "31"))
                return 3
                
            print(color_text(f"Running live evaluation with adapter '{args.adapter}'...", "36"))
            for case in suite_obj.cases:
                print(color_text(f"  Generating answer for case: {case.id}...", "90"))
                try:
                    resp = adapter_obj.generate(case)
                    answers_dict[case.id] = answer_from_response(case, resp)
                except Exception as e:
                    print(color_text(f"  Error generating answer for case '{case.id}': {e}", "31"))
                    # Create an empty/error answer so rules fail rather than crashing
                    from .models import Answer
                    answers_dict[case.id] = Answer(case_id=case.id, output=f"Error: {e}")
            
            # Save generated answers if requested
            if args.save_answers:
                serializable_answers = [
                    {
                        "case_id": ans.case_id,
                        "output": ans.output,
                        "citations": ans.citations,
                        "metadata": ans.metadata
                    }
                    for ans in answers_dict.values()
                ]
                try:
                    Path(args.save_answers).write_text(
                        json.dumps({"answers": serializable_answers}, indent=2, ensure_ascii=False),
                        encoding="utf-8"
                    )
                    print(color_text(f"Generated answers saved to: {args.save_answers}", "32"))
                except Exception as e:
                    print(color_text(f"Error saving generated answers: {e}", "31"))
        else:
            print(color_text("Error: Either --answers or --adapter must be provided to run tests.", "31"))
            return 2

        # Initialize judge if specified
        judge_obj = None
        if args.judge_adapter:
            try:
                judge_obj = get_adapter(args.judge_adapter, model=args.judge_model)
            except Exception as e:
                print(color_text(f"Error initializing judge adapter: {e}", "31"))
                return 3
        
        report = evaluate_suite(suite_obj, answers_dict, judge=judge_obj)
        
        # Output reports
        if args.html:
            try:
                generate_html_report(report, args.html)
                print(color_text(f"HTML report written to: {args.html}", "32"))
            except Exception as e:
                print(color_text(f"Error generating HTML report: {e}", "31"))
                
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            summary_color = "1;32" if report.ok else "1;31"
            print(color_text(f"PromptWatch: {report.passed} passed, {report.failed} failed", summary_color))
            for case in report.cases:
                marker = color_text("PASS", "32") if case.passed else color_text("FAIL", "31")
                print(f"{marker} {case.case_id}")
                for check in case.checks:
                    if not check.passed:
                        print(color_text(f"  - {check.message}", "33"))
        return 0 if report.ok else 1

    elif args.command == "compare":
        try:
            old = load_answers(args.old_answers)
            new = load_answers(args.new_answers)
        except Exception as e:
            print(color_text(f"Error loading answers files: {e}", "31"))
            return 3
            
        all_ids = sorted(list(set(old.keys()) | set(new.keys())))
        identical = []
        changed = []
        added = []
        removed = []
        
        for case_id in all_ids:
            in_old = case_id in old
            in_new = case_id in new
            if in_old and in_new:
                if old[case_id].output == new[case_id].output:
                    identical.append(case_id)
                else:
                    changed.append(case_id)
            elif in_new:
                added.append(case_id)
            else:
                removed.append(case_id)
                
        # Terminal Summary
        print(color_text("PromptWatch Run Comparison Report", "1;36"))
        print(color_text("======================================", "36"))
        print(color_text(f"Identical answers: {len(identical)}", "90" if identical else "0"))
        print(color_text(f"Changed answers:   {len(changed)}", "1;33" if changed else "0"))
        print(color_text(f"Added cases:       {len(added)}", "1;32" if added else "0"))
        print(color_text(f"Removed cases:     {len(removed)}", "1;31" if removed else "0"))
        print()
        
        if changed:
            print(color_text("Changed cases:", "33"))
            for case_id in changed:
                print(f"  * {case_id}")
        if added:
            print(color_text("Added cases:", "32"))
            for case_id in added:
                print(f"  * {case_id} [New]")
        if removed:
            print(color_text("Removed cases:", "31"))
            for case_id in removed:
                print(f"  * {case_id} [Deleted]")
                
        if args.html:
            try:
                generate_comparison_report(old, new, args.html)
                print(color_text(f"\nVisual HTML comparison report written to: {args.html}", "32"))
            except Exception as e:
                print(color_text(f"Error generating comparison HTML report: {e}", "31"))
                
        return 0 if not changed else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
