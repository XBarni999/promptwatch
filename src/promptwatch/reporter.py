from __future__ import annotations

import html
import json
import difflib
from pathlib import Path
from typing import Any
from .engine import EvaluationReport
from .models import Answer

def generate_html_report(report: EvaluationReport, output_path: str) -> None:
    pass_rate = (report.passed / report.total * 100) if report.total > 0 else 0
    status_class = "pass" if report.ok else "fail"
    status_text = "PASSED" if report.ok else "FAILED"
    
    cases_html = []
    for case in report.cases:
        case_status = "passed" if case.passed else "failed"
        case_badge = "PASS" if case.passed else "FAIL"
        
        checks_rows = []
        for check in case.checks:
            chk_status = "PASS" if check.passed else "FAIL"
            chk_class = "check-pass" if check.passed else "check-fail"
            checks_rows.append(f"""
                <tr class="{chk_class}">
                    <td class="check-name">{html.escape(check.name)}</td>
                    <td class="check-status-badge">{chk_status}</td>
                    <td class="check-message">{html.escape(check.message)}</td>
                </tr>
            """)
            
        checks_table = f"""
            <table class="checks-table">
                <thead>
                    <tr>
                        <th>Rule</th>
                        <th>Status</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(checks_rows)}
                </tbody>
            </table>
        """ if checks_rows else "<p class='no-checks'>No checks were run.</p>"

        # Find if output exists, or errors
        output_text = ""
        citations_html = ""
        metadata_html = ""
        
        cases_html.append(f"""
        <div class="case-card {case_status}" data-case-id="{html.escape(case.case_id)}">
            <div class="case-header" onclick="toggleAccordion(this)">
                <span class="status-badge {case_status}">{case_badge}</span>
                <span class="case-title">{html.escape(case.case_id)}</span>
                <span class="arrow">&#9662;</span>
            </div>
            <div class="case-body">
                <div class="details-section">
                    <h4>Prompt Input</h4>
                    <pre class="input-display">{html.escape(case.input)}</pre>
                </div>
                <div class="details-section">
                    <h4>Model Output</h4>
                    <pre class="output-display">{html.escape(case.output)}</pre>
                </div>
                <div class="details-section">
                    <h4>Expected Checks Summary</h4>
                    {checks_table}
                </div>
            </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptWatch Test Report - {html.escape(report.suite_name)}</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --pass-color: #10b981;
            --pass-bg: rgba(16, 185, 129, 0.1);
            --fail-color: #ef4444;
            --fail-bg: rgba(239, 68, 68, 0.1);
            --primary-color: #6366f1;
            --primary-hover: #4f46e5;
        }}
        
        [data-theme="light"] {{
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-color: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --pass-bg: rgba(16, 185, 129, 0.15);
            --fail-bg: rgba(239, 68, 68, 0.15);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.5;
            padding: 2rem 1rem;
            transition: background-color 0.3s, color 0.3s;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
        }}

        .title-section h1 {{
            font-size: 2rem;
            font-weight: 700;
        }}
        
        .title-section p {{
            color: var(--text-muted);
            margin-top: 0.25rem;
        }}

        .theme-toggle {{
            background: none;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }}

        .theme-toggle:hover {{
            background-color: var(--border-color);
        }}

        /* Dashboard widgets */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .widget {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1.5rem;
            text-align: center;
            position: relative;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .widget h3 {{
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .widget-val {{
            font-size: 2.25rem;
            font-weight: 800;
        }}

        .widget-val.pass-text {{
            color: var(--pass-color);
        }}

        .widget-val.fail-text {{
            color: var(--fail-color);
        }}

        /* Controls */
        .controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}

        .filter-tabs {{
            display: flex;
            gap: 0.5rem;
        }}

        .tab-btn {{
            background: none;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .tab-btn:hover {{
            background-color: var(--border-color);
        }}

        .tab-btn.active {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            color: white;
        }}

        .search-bar {{
            flex-grow: 1;
            max-width: 400px;
            position: relative;
        }}

        .search-bar input {{
            width: 100%;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            transition: all 0.2s;
        }}

        .search-bar input:focus {{
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }}

        /* Case list */
        .case-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .case-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .case-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        }}

        .case-card.passed {{
            border-left: 4px solid var(--pass-color);
        }}

        .case-card.failed {{
            border-left: 4px solid var(--fail-color);
        }}

        .case-header {{
            display: flex;
            align-items: center;
            padding: 1rem 1.5rem;
            cursor: pointer;
            user-select: none;
        }}

        .status-badge {{
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            margin-right: 1rem;
            text-transform: uppercase;
        }}

        .status-badge.passed {{
            background-color: var(--pass-bg);
            color: var(--pass-color);
        }}

        .status-badge.failed {{
            background-color: var(--fail-bg);
            color: var(--fail-color);
        }}

        .case-title {{
            font-weight: 600;
            font-size: 1.1rem;
            flex-grow: 1;
        }}

        .arrow {{
            font-size: 1.25rem;
            transition: transform 0.2s;
        }}

        .case-card.active .arrow {{
            transform: rotate(180deg);
        }}

        .case-body {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
            padding: 0 1.5rem;
            border-top: 1px solid transparent;
        }}

        .case-card.active .case-body {{
            max-height: 2000px;
            padding: 1.5rem;
            border-top: 1px solid var(--border-color);
        }}

        .details-section {{
            margin-bottom: 1.5rem;
        }}

        .details-section:last-child {{
            margin-bottom: 0;
        }}

        .details-section h4 {{
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.25rem;
        }}

        /* Table of checks */
        .checks-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }}

        .checks-table th, .checks-table td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}

        .checks-table th {{
            font-weight: 600;
            color: var(--text-muted);
        }}

        .check-pass td.check-status-badge {{
            color: var(--pass-color);
            font-weight: 700;
        }}

        .check-fail td.check-status-badge {{
            color: var(--fail-color);
            font-weight: 700;
        }}

        .check-message {{
            font-family: inherit;
        }}

        .no-checks {{
            color: var(--text-muted);
            font-style: italic;
        }}

        .input-display, .output-display {{
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.875rem;
            padding: 1rem;
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 0.375rem;
            overflow-x: auto;
            white-space: pre-wrap;
            border: 1px solid var(--border-color);
            margin-top: 0.25rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="title-section">
                <h1>PromptWatch Test Suite</h1>
                <p>Suite: <strong>{html.escape(report.suite_name)}</strong></p>
            </div>
            <button class="theme-toggle" onclick="toggleTheme()">Toggle Light Theme</button>
        </header>

        <section class="dashboard">
            <div class="widget">
                <h3>Pass Rate</h3>
                <div class="widget-val {status_class}-text">{pass_rate:.1f}%</div>
            </div>
            <div class="widget">
                <h3>Total Cases</h3>
                <div class="widget-val">{report.total}</div>
            </div>
            <div class="widget">
                <h3>Passed</h3>
                <div class="widget-val pass-text">{report.passed}</div>
            </div>
            <div class="widget">
                <h3>Failed</h3>
                <div class="widget-val fail-text">{report.failed}</div>
            </div>
        </section>

        <section class="controls">
            <div class="filter-tabs">
                <button class="tab-btn active" onclick="filterCases('all', this)">All</button>
                <button class="tab-btn" onclick="filterCases('passed', this)">Passed</button>
                <button class="tab-btn" onclick="filterCases('failed', this)">Failed</button>
            </div>
            <div class="search-bar">
                <input type="text" placeholder="Search case ID..." onkeyup="searchCases(this.value)">
            </div>
        </section>

        <section class="case-list">
            {"".join(cases_html)}
        </section>
    </div>

    <script>
        function toggleTheme() {{
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "light" ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", newTheme);
            document.querySelector(".theme-toggle").textContent = 
                newTheme === "light" ? "Toggle Dark Theme" : "Toggle Light Theme";
        }}

        function toggleAccordion(header) {{
            const card = header.parentElement;
            card.classList.toggle("active");
        }}

        function filterCases(filter, button) {{
            // Update tabs
            document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");

            // Filter cards
            document.querySelectorAll(".case-card").forEach(card => {{
                if (filter === "all") {{
                    card.style.display = "";
                }} else if (filter === "passed" && card.classList.contains("passed")) {{
                    card.style.display = "";
                }} else if (filter === "failed" && card.classList.contains("failed")) {{
                    card.style.display = "";
                }} else {{
                    card.style.display = "none";
                }}
            }});
        }}

        function searchCases(query) {{
            query = query.toLowerCase();
            const activeTab = document.querySelector(".tab-btn.active").textContent.toLowerCase();
            
            document.querySelectorAll(".case-card").forEach(card => {{
                const caseId = card.getAttribute("data-case-id").toLowerCase();
                const matchesSearch = caseId.includes(query);
                
                let matchesTab = false;
                if (activeTab === "all") matchesTab = true;
                else if (activeTab === "passed" && card.classList.contains("passed")) matchesTab = true;
                else if (activeTab === "failed" && card.classList.contains("failed")) matchesTab = true;

                if (matchesSearch && matchesTab) {{
                    card.style.display = "";
                }} else {{
                    card.style.display = "none";
                }}
            }});
        }}
    </script>
</body>
</html>
"""
    Path(output_path).write_text(html_content, encoding="utf-8")


def generate_comparison_report(old_answers: dict[str, Answer], new_answers: dict[str, Answer], output_path: str) -> None:
    cases_diffs = []
    
    all_case_ids = sorted(list(set(old_answers.keys()) | set(new_answers.keys())))
    identical_count = 0
    changed_count = 0
    added_count = 0
    removed_count = 0
    
    for case_id in all_case_ids:
        in_old = case_id in old_answers
        in_new = case_id in new_answers
        
        diff_html = ""
        case_status = ""
        badge_text = ""
        
        if in_old and in_new:
            old_output = old_answers[case_id].output
            new_output = new_answers[case_id].output
            
            if old_output == new_output:
                identical_count += 1
                case_status = "identical"
                badge_text = "IDENTICAL"
                diff_html = f"""
                <div class="diff-wrapper single">
                    <pre class="identical-code">{html.escape(old_output)}</pre>
                </div>
                """
            else:
                changed_count += 1
                case_status = "changed"
                badge_text = "CHANGED"
                
                # Generate a side by side line diff using difflib
                old_lines = old_output.splitlines()
                new_lines = new_output.splitlines()
                
                # Make inline word diffs or simple line diff
                diff_lines = list(difflib.ndiff(old_lines, new_lines))
                
                old_column = []
                new_column = []
                
                for line in diff_lines:
                    if line.startswith("- "):
                        old_column.append(f'<span class="del">{html.escape(line[2:])}</span>')
                    elif line.startswith("+ "):
                        new_column.append(f'<span class="add">{html.escape(line[2:])}</span>')
                    elif line.startswith("  "):
                        old_column.append(html.escape(line[2:]))
                        new_column.append(html.escape(line[2:]))
                        
                diff_html = f"""
                <div class="diff-wrapper split">
                    <div class="diff-pane">
                        <h5>Before (Old)</h5>
                        <pre class="diff-pre">{"<br>".join(old_column) if old_column else "<em>Empty</em>"}</pre>
                    </div>
                    <div class="diff-pane">
                        <h5>After (New)</h5>
                        <pre class="diff-pre">{"<br>".join(new_column) if new_column else "<em>Empty</em>"}</pre>
                    </div>
                </div>
                """
        elif in_new:
            added_count += 1
            case_status = "added"
            badge_text = "ADDED"
            diff_html = f"""
            <div class="diff-wrapper single">
                <pre class="added-code">{html.escape(new_answers[case_id].output)}</pre>
            </div>
            """
        else:
            removed_count += 1
            case_status = "removed"
            badge_text = "REMOVED"
            diff_html = f"""
            <div class="diff-wrapper single">
                <pre class="removed-code">{html.escape(old_answers[case_id].output)}</pre>
            </div>
            """
            
        cases_diffs.append(f"""
        <div class="case-card {case_status}" data-case-id="{html.escape(case_id)}">
            <div class="case-header" onclick="toggleAccordion(this)">
                <span class="status-badge {case_status}">{badge_text}</span>
                <span class="case-title">{html.escape(case_id)}</span>
                <span class="arrow">&#9662;</span>
            </div>
            <div class="case-body">
                {diff_html}
            </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptWatch Run Comparison</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --pass-color: #10b981;
            --pass-bg: rgba(16, 185, 129, 0.1);
            --fail-color: #ef4444;
            --fail-bg: rgba(239, 68, 68, 0.1);
            
            --identical-color: #94a3b8;
            --identical-bg: rgba(148, 163, 184, 0.1);
            --changed-color: #f59e0b;
            --changed-bg: rgba(245, 158, 11, 0.15);
            --added-color: #10b981;
            --added-bg: rgba(16, 185, 129, 0.15);
            --removed-color: #ef4444;
            --removed-bg: rgba(239, 68, 68, 0.15);
            
            --primary-color: #6366f1;
            --primary-hover: #4f46e5;
        }}
        
        [data-theme="light"] {{
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-color: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.5;
            padding: 2rem 1rem;
            transition: background-color 0.3s, color 0.3s;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
        }}

        .title-section h1 {{
            font-size: 2rem;
            font-weight: 700;
        }}
        
        .title-section p {{
            color: var(--text-muted);
            margin-top: 0.25rem;
        }}

        .theme-toggle {{
            background: none;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }}

        .theme-toggle:hover {{
            background-color: var(--border-color);
        }}

        /* Dashboard widgets */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .widget {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .widget h3 {{
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .widget-val {{
            font-size: 2rem;
            font-weight: 800;
        }}

        .widget-val.changed-text {{
            color: var(--changed-color);
        }}
        .widget-val.added-text {{
            color: var(--added-color);
        }}
        .widget-val.removed-text {{
            color: var(--removed-color);
        }}

        /* Controls */
        .controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}

        .filter-tabs {{
            display: flex;
            gap: 0.5rem;
        }}

        .tab-btn {{
            background: none;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .tab-btn:hover {{
            background-color: var(--border-color);
        }}

        .tab-btn.active {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            color: white;
        }}

        .search-bar {{
            flex-grow: 1;
            max-width: 400px;
        }}

        .search-bar input {{
            width: 100%;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            transition: all 0.2s;
        }}

        .search-bar input:focus {{
            outline: none;
            border-color: var(--primary-color);
        }}

        /* Case list */
        .case-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .case-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}

        .case-card.identical {{
            border-left: 4px solid var(--identical-color);
        }}
        .case-card.changed {{
            border-left: 4px solid var(--changed-color);
        }}
        .case-card.added {{
            border-left: 4px solid var(--added-color);
        }}
        .case-card.removed {{
            border-left: 4px solid var(--removed-color);
        }}

        .case-header {{
            display: flex;
            align-items: center;
            padding: 1rem 1.5rem;
            cursor: pointer;
            user-select: none;
        }}

        .status-badge {{
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            margin-right: 1rem;
            text-transform: uppercase;
        }}

        .status-badge.identical {{
            background-color: var(--identical-bg);
            color: var(--identical-color);
        }}
        .status-badge.changed {{
            background-color: var(--changed-bg);
            color: var(--changed-color);
        }}
        .status-badge.added {{
            background-color: var(--added-bg);
            color: var(--added-color);
        }}
        .status-badge.removed {{
            background-color: var(--removed-bg);
            color: var(--removed-color);
        }}

        .case-title {{
            font-weight: 600;
            font-size: 1.1rem;
            flex-grow: 1;
        }}

        .arrow {{
            font-size: 1.25rem;
            transition: transform 0.2s;
        }}

        .case-card.active .arrow {{
            transform: rotate(180deg);
        }}

        .case-body {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
            padding: 0 1.5rem;
        }}

        .case-card.active .case-body {{
            max-height: 3000px;
            padding: 1.5rem;
            border-top: 1px solid var(--border-color);
        }}

        /* Diff UI */
        .diff-wrapper {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .diff-wrapper.split {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }}

        @media (max-width: 768px) {{
            .diff-wrapper.split {{
                grid-template-columns: 1fr;
            }}
        }}

        .diff-pane h5 {{
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}

        .diff-pre, .identical-code, .added-code, .removed-code {{
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.875rem;
            padding: 1rem;
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 0.375rem;
            overflow-x: auto;
            white-space: pre-wrap;
            border: 1px solid var(--border-color);
        }}

        .diff-pre span.add {{
            background-color: var(--added-bg);
            color: #34d399;
            font-weight: 600;
            display: block;
            padding: 0.1rem 0;
        }}

        .diff-pre span.del {{
            background-color: var(--removed-bg);
            color: #f87171;
            font-weight: 600;
            display: block;
            padding: 0.1rem 0;
        }}

        .added-code {{
            border-left: 3px solid var(--added-color);
            background-color: var(--added-bg);
        }}

        .removed-code {{
            border-left: 3px solid var(--removed-color);
            background-color: var(--removed-bg);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="title-section">
                <h1>PromptWatch Run Comparison</h1>
                <p>Comparing output snapshots</p>
            </div>
            <button class="theme-toggle" onclick="toggleTheme()">Toggle Light Theme</button>
        </header>

        <section class="dashboard">
            <div class="widget">
                <h3>Identical</h3>
                <div class="widget-val">{identical_count}</div>
            </div>
            <div class="widget">
                <h3>Changed</h3>
                <div class="widget-val changed-text">{changed_count}</div>
            </div>
            <div class="widget">
                <h3>Added</h3>
                <div class="widget-val added-text">{added_count}</div>
            </div>
            <div class="widget">
                <h3>Removed</h3>
                <div class="widget-val removed-text">{removed_count}</div>
            </div>
        </section>

        <section class="controls">
            <div class="filter-tabs">
                <button class="tab-btn active" onclick="filterCases('all', this)">All</button>
                <button class="tab-btn" onclick="filterCases('changed', this)">Changed</button>
                <button class="tab-btn" onclick="filterCases('identical', this)">Identical</button>
            </div>
            <div class="search-bar">
                <input type="text" placeholder="Search case ID..." onkeyup="searchCases(this.value)">
            </div>
        </section>

        <section class="case-list">
            {"".join(cases_diffs)}
        </section>
    </div>

    <script>
        function toggleTheme() {{
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "light" ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", newTheme);
            document.querySelector(".theme-toggle").textContent = 
                newTheme === "light" ? "Toggle Dark Theme" : "Toggle Light Theme";
        }}

        function toggleAccordion(header) {{
            const card = header.parentElement;
            card.classList.toggle("active");
        }}

        function filterCases(filter, button) {{
            document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");

            document.querySelectorAll(".case-card").forEach(card => {{
                if (filter === "all") {{
                    card.style.display = "";
                }} else if (filter === "changed" && card.classList.contains("changed")) {{
                    card.style.display = "";
                }} else if (filter === "identical" && card.classList.contains("identical")) {{
                    card.style.display = "";
                }} else {{
                    card.style.display = "none";
                }}
            }});
        }}

        function searchCases(query) {{
            query = query.toLowerCase();
            const activeTab = document.querySelector(".tab-btn.active").textContent.toLowerCase();
            
            document.querySelectorAll(".case-card").forEach(card => {{
                const caseId = card.getAttribute("data-case-id").toLowerCase();
                const matchesSearch = caseId.includes(query);
                
                let matchesTab = false;
                if (activeTab === "all") matchesTab = true;
                else if (activeTab === "changed" && card.classList.contains("changed")) matchesTab = true;
                else if (activeTab === "identical" && card.classList.contains("identical")) matchesTab = true;

                if (matchesSearch && matchesTab) {{
                    card.style.display = "";
                }} else {{
                    card.style.display = "none";
                }}
            }});
        }}
    </script>
</body>
</html>
"""
    Path(output_path).write_text(html_content, encoding="utf-8")
