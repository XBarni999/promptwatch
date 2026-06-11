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


class MainMenuRedirect(Exception):
    pass


class ExitCLI(Exception):
    pass


def prompt_input(prompt_text: str, default: str | None = None, allow_back: bool = True) -> str:
    try:
        val = input(prompt_text).strip()
    except (KeyboardInterrupt, EOFError):
        raise ExitCLI()
    
    if allow_back and val.lower() in ("0", "q", "back", "exit"):
        raise MainMenuRedirect()
        
    if not val and default is not None:
        return default
    return val


def run_interactive_menu() -> int:
    while True:
        print("\n" + color_text("=== PromptWatch Interactive CLI Menu ===", "1;36"))
        print("Please select an option:")
        print("  1) Run a test suite (live execution or offline answers)")
        print("  2) Compare two runs side-by-side (diff)")
        print("  3) Configure your API keys locally")
        print("  4) Exit")
        print(color_text("  (At any prompt, type '0', 'q', 'back', or 'exit' to return to this menu)", "90"))
        print()
        
        try:
            choice = prompt_input(color_text("Enter choice (1-4): ", "1;33"), allow_back=False)
        except ExitCLI:
            print(color_text("\nGoodbye!", "36"))
            return 0
            
        if choice == "4":
            print(color_text("Goodbye!", "36"))
            return 0
        elif choice not in ("1", "2", "3"):
            print(color_text("Invalid selection.", "31"))
            continue

        try:
            if choice == "1":
                # Run a test suite
                suite_path = prompt_input(
                    color_text("Enter path to test suite YAML/JSON file (default: examples/rag_support.yaml): ", "36"),
                    default="examples/rag_support.yaml"
                )
                if not Path(suite_path).exists():
                    print(color_text(f"Error: File not found: {suite_path}", "31"))
                    continue

                print("\nSelect execution mode:")
                print("  1) Run using a saved answers JSON file (Offline Mode)")
                print("  2) Run live using a cloud LLM adapter (OpenAI, Groq, OpenRouter) or HTTP endpoint")
                mode = prompt_input(color_text("Enter choice (1-2): ", "1;33"))
                
                answers_dict = {}
                adapter_name = None
                model_name = None
                url = None
                json_path = None
                save_answers_path = None

                if mode == "1":
                    answers_path = prompt_input(
                        color_text("Enter path to answers JSON file (default: examples/answers.json): ", "36"),
                        default="examples/answers.json"
                    )
                    if not Path(answers_path).exists():
                        print(color_text(f"Error: File not found: {answers_path}", "31"))
                        continue
                    answers_dict = load_answers(answers_path)
                elif mode == "2":
                    print("\nSelect adapter type:")
                    print("  1) OpenAI")
                    print("  2) Groq")
                    print("  3) OpenRouter")
                    print("  4) Custom HTTP API")
                    adapter_choice = prompt_input(color_text("Enter choice (1-4): ", "1;33"))
                    if adapter_choice == "1":
                        adapter_name = "openai"
                        model_name = prompt_input(
                            color_text("Enter model name (default: gpt-4o-mini): ", "36"),
                            default="gpt-4o-mini"
                        )
                    elif adapter_choice == "2":
                        adapter_name = "groq"
                        model_name = prompt_input(
                            color_text("Enter model name (default: llama-3.3-70b-versatile): ", "36"),
                            default="llama-3.3-70b-versatile"
                        )
                    elif adapter_choice == "3":
                        adapter_name = "openrouter"
                        model_name = prompt_input(
                            color_text("Enter model name (default: google/gemini-2.5-flash): ", "36"),
                            default="google/gemini-2.5-flash"
                        )
                    elif adapter_choice == "4":
                        adapter_name = "http"
                        url = prompt_input(color_text("Enter HTTP API URL (e.g. http://localhost:8000/chat): ", "36"))
                        if not url:
                            print(color_text("Error: URL is required for HTTP adapter.", "31"))
                            continue
                        json_path = prompt_input(
                            color_text("Enter JSON dot-path to output field (optional): ", "36"),
                            default=""
                        ) or None
                    else:
                        print(color_text("Invalid choice.", "31"))
                        continue

                    save_answers = prompt_input(
                        color_text("Do you want to save the generated responses to a JSON file? (y/n): ", "36")
                    ).lower()
                    if save_answers in ("y", "yes"):
                        save_answers_path = prompt_input(
                            color_text("Enter output JSON path (default: my_answers.json): ", "36"),
                            default="my_answers.json"
                        )
                else:
                    print(color_text("Invalid choice.", "31"))
                    continue

                # Ask for semantic judge
                judge_obj = None
                use_judge = prompt_input(
                    color_text("Do you want to run semantic checks using an LLM judge? (y/n): ", "36")
                ).lower()
                if use_judge in ("y", "yes"):
                    print("\nSelect judge API:")
                    print("  1) OpenAI (defaults to gpt-4o-mini)")
                    print("  2) Groq (defaults to llama-3.3-70b-versatile)")
                    print("  3) OpenRouter (defaults to google/gemini-2.5-flash)")
                    judge_choice = prompt_input(color_text("Enter choice (1-3): ", "1;33"))
                    ja_name = "openai" if judge_choice == "1" else "groq" if judge_choice == "2" else "openrouter" if judge_choice == "3" else None
                    if ja_name:
                        try:
                            judge_obj = get_adapter(ja_name)
                        except Exception as e:
                            print(color_text(f"Error initializing judge: {e}", "31"))
                            continue
                    else:
                        print(color_text("Invalid choice.", "31"))
                        continue

                # Ask for HTML report
                html_report_path = None
                gen_html = prompt_input(
                    color_text("Do you want to generate a premium visual HTML report? (y/n): ", "36")
                ).lower()
                if gen_html in ("y", "yes"):
                    html_report_path = prompt_input(
                        color_text("Enter HTML report output path (default: report.html): ", "36"),
                        default="report.html"
                    )

                # Now execute run command
                suite_obj = load_suite(suite_path)
                if adapter_name:
                    try:
                        adapter_obj = get_adapter(adapter_name, model=model_name, url=url, json_path=json_path)
                    except Exception as e:
                        print(color_text(f"Error initializing adapter: {e}", "31"))
                        continue
                        
                    print(color_text(f"\nRunning live evaluation with adapter '{adapter_name}'...", "36"))
                    for case in suite_obj.cases:
                        print(color_text(f"  Generating answer for case: {case.id}...", "90"))
                        try:
                            resp = adapter_obj.generate(case)
                            answers_dict[case.id] = answer_from_response(case, resp)
                        except Exception as e:
                            print(color_text(f"  Error generating answer for case '{case.id}': {e}", "31"))
                            from .models import Answer
                            answers_dict[case.id] = Answer(case_id=case.id, output=f"Error: {e}")
                    
                    if save_answers_path:
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
                            Path(save_answers_path).write_text(
                                json.dumps({"answers": serializable_answers}, indent=2, ensure_ascii=False),
                                encoding="utf-8"
                            )
                            print(color_text(f"Generated answers saved to: {save_answers_path}", "32"))
                        except Exception as e:
                            print(color_text(f"Error saving generated answers: {e}", "31"))

                report = evaluate_suite(suite_obj, answers_dict, judge=judge_obj)
                
                if html_report_path:
                    try:
                        generate_html_report(report, html_report_path)
                        print(color_text(f"HTML report written to: {html_report_path}", "32"))
                    except Exception as e:
                        print(color_text(f"Error generating HTML report: {e}", "31"))

                summary_color = "1;32" if report.ok else "1;31"
                print("\n" + color_text("=== Suite Results ===", "1;36"))
                print(color_text(f"PromptWatch: {report.passed} passed, {report.failed} failed", summary_color))
                for case in report.cases:
                    marker = color_text("PASS", "32") if case.passed else color_text("FAIL", "31")
                    print(f"{marker} {case.case_id}")
                    for check in case.checks:
                        if not check.passed:
                            print(color_text(f"  - {check.message}", "33"))
                
                prompt_input(color_text("\nPress Enter to return to the main menu...", "36"), allow_back=False)
                continue

            elif choice == "2":
                # Compare runs
                old_path = prompt_input(color_text("Enter path to older answers JSON file: ", "36"))
                if not Path(old_path).exists():
                    print(color_text(f"Error: File not found: {old_path}", "31"))
                    continue
                new_path = prompt_input(color_text("Enter path to newer answers JSON file: ", "36"))
                if not Path(new_path).exists():
                    print(color_text(f"Error: File not found: {new_path}", "31"))
                    continue
                    
                html_report_path = prompt_input(
                    color_text("Enter HTML diff output path (default: diff.html): ", "36"),
                    default="diff.html"
                )
                
                old = load_answers(old_path)
                new = load_answers(new_path)
                
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
                        
                print("\n" + color_text("PromptWatch Run Comparison Report", "1;36"))
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
                        
                try:
                    generate_comparison_report(old, new, html_report_path)
                    print(color_text(f"\nVisual HTML comparison report written to: {html_report_path}", "32"))
                except Exception as e:
                    print(color_text(f"Error generating comparison HTML report: {e}", "31"))
                    
                prompt_input(color_text("\nPress Enter to return to the main menu...", "36"), allow_back=False)
                continue

            elif choice == "3":
                # Setup API keys
                print("\nSelect API key to configure:")
                print("  1) OpenAI")
                print("  2) Groq")
                print("  3) OpenRouter")
                api_choice = prompt_input(color_text("Enter choice (1-3): ", "1;33"))
                
                key = prompt_input(color_text("Enter API key (press Enter to clear key): ", "36"))
                
                if api_choice == "1":
                    from .config import set_openai_api_key
                    set_openai_api_key(key)
                    print(color_text("OpenAI API key updated.", "32"))
                elif api_choice == "2":
                    from .config import set_groq_api_key
                    set_groq_api_key(key)
                    print(color_text("Groq API key updated.", "32"))
                elif api_choice == "3":
                    from .config import set_openrouter_api_key
                    set_openrouter_api_key(key)
                    print(color_text("OpenRouter API key updated.", "32"))
                else:
                    print(color_text("Invalid choice.", "31"))
                    
                prompt_input(color_text("\nPress Enter to return to the main menu...", "36"), allow_back=False)
                continue

        except MainMenuRedirect:
            print(color_text("\nReturning to main menu...", "33"))
            continue
        except ExitCLI:
            print(color_text("\nGoodbye!", "36"))
            return 0


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
    parser.add_argument("--setup-openai", help="Save your OpenAI API key locally.")
    parser.add_argument("--setup-openrouter", help="Save your OpenRouter API key locally.")
    parser.add_argument("--setup-groq", help="Save your Groq API key locally.")
    
    subparsers = parser.add_subparsers(dest="command", required=False)

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
    
    if args.setup_openai is not None:
        from .config import set_openai_api_key
        set_openai_api_key(args.setup_openai)
        if args.setup_openai.strip():
            print(color_text("OpenAI API key saved successfully.", "32"))
        else:
            print(color_text("OpenAI API key cleared.", "32"))
        return 0

    if args.setup_openrouter is not None:
        from .config import set_openrouter_api_key
        set_openrouter_api_key(args.setup_openrouter)
        if args.setup_openrouter.strip():
            print(color_text("OpenRouter API key saved successfully.", "32"))
        else:
            print(color_text("OpenRouter API key cleared.", "32"))
        return 0

    if args.setup_groq is not None:
        from .config import set_groq_api_key
        set_groq_api_key(args.setup_groq)
        if args.setup_groq.strip():
            print(color_text("Groq API key saved successfully.", "32"))
        else:
            print(color_text("Groq API key cleared.", "32"))
        return 0

    if not args.command:
        return run_interactive_menu()

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
