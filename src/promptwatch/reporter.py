from __future__ import annotations

import html
import json
import difflib
from pathlib import Path
from .engine import EvaluationReport
from .models import Answer

def generate_html_report(report: EvaluationReport, output_path: str) -> None:
    pass_rate = (report.passed / report.total * 100) if report.total > 0 else 0
    status_class = "pass" if report.ok else "fail"
    status_text = "Passed" if report.ok else "Failed"
    
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
        
        cases_html.append(f"""
        <div class="case-card {case_status}" data-case-id="{html.escape(case.case_id)}">
            <div class="case-header" onclick="toggleAccordion(this)">
                <div class="case-header-left">
                    <span class="status-indicator {case_status}"></span>
                    <span class="case-title">{html.escape(case.case_id)}</span>
                </div>
                <div class="case-header-right">
                    <span class="status-pill {case_status}">{case_badge}</span>
                    <span class="arrow">&#9662;</span>
                </div>
            </div>
            <div class="case-body">
                <div class="case-grid">
                    <div class="case-grid-left">
                        <div class="code-container">
                            <div class="code-header">Prompt Input</div>
                            <pre class="code-display">{html.escape(case.input)}</pre>
                        </div>
                        <div class="code-container">
                            <div class="code-header">Model Output</div>
                            <pre class="code-display output-pre">{html.escape(case.output)}</pre>
                        </div>
                    </div>
                    <div class="case-grid-right">
                        <div class="rules-section">
                            <div class="rules-header">Validation Checks</div>
                            {checks_table}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptWatch - {html.escape(report.suite_name)}</title>
    <style>
        :root {{
            --bg-color: #09090b;
            --card-bg: #18181b;
            --card-hover-border: #27272a;
            --text-color: #fafafa;
            --text-muted: #a1a1aa;
            --border-color: #27272a;
            
            --pass-color: #10b981;
            --pass-bg: rgba(16, 185, 129, 0.1);
            --fail-color: #ef4444;
            --fail-bg: rgba(239, 68, 68, 0.1);
            
            --primary-color: #3f3f46;
            --primary-hover: #52525b;
            --accent-color: #ffffff;
            
            --code-bg: #09090b;
        }}
        
        [data-theme="light"] {{
            --bg-color: #fafafa;
            --card-bg: #ffffff;
            --card-hover-border: #e4e4e7;
            --text-color: #09090b;
            --text-muted: #71717a;
            --border-color: #e4e4e7;
            --pass-bg: rgba(16, 185, 129, 0.15);
            --fail-bg: rgba(239, 68, 68, 0.15);
            --code-bg: #f4f4f5;
            --primary-color: #e4e4e7;
            --primary-hover: #d4d4d8;
            --accent-color: #09090b;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 3rem 1.5rem;
            transition: background-color 0.2s, color 0.2s;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .logo-section {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .logo-title {{
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: var(--text-color);
        }}

        .suite-badge {{
            font-size: 0.75rem;
            background-color: var(--border-color);
            color: var(--text-muted);
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            font-weight: 500;
        }}

        .theme-toggle {{
            background: none;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: background-color 0.2s;
        }}

        .theme-toggle:hover {{
            background-color: var(--card-bg);
        }}

        /* Dashboard grid */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            border: 1px solid var(--border-color);
            background-color: var(--card-bg);
            border-radius: 8px;
            margin-bottom: 3rem;
            overflow: hidden;
        }}

        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        .widget {{
            padding: 2rem 1.5rem;
            text-align: left;
            border-right: 1px solid var(--border-color);
        }}

        .widget:last-child {{
            border-right: none;
        }}

        .widget h3 {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}

        .widget-val {{
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.025em;
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
            gap: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }}

        .filter-tabs {{
            display: flex;
            gap: 0.35rem;
            background-color: var(--card-bg);
            padding: 0.25rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .tab-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 0.4rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .tab-btn:hover {{
            color: var(--text-color);
        }}

        .tab-btn.active {{
            background-color: var(--bg-color);
            color: var(--text-color);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        .search-bar {{
            flex-grow: 1;
            max-width: 350px;
        }}

        .search-bar input {{
            width: 100%;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.55rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            transition: all 0.2s;
        }}

        .search-bar input:focus {{
            outline: none;
            border-color: var(--accent-color);
        }}

        /* Case list */
        .case-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .case-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            transition: border-color 0.2s;
        }}

        .case-card:hover {{
            border-color: var(--card-hover-border);
        }}

        .case-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.25rem 1.5rem;
            cursor: pointer;
            user-select: none;
        }}

        .case-header-left {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .case-header-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .status-indicator {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}

        .status-indicator.passed {{
            background-color: var(--pass-color);
        }}

        .status-indicator.failed {{
            background-color: var(--fail-color);
        }}

        .case-title {{
            font-weight: 600;
            font-size: 0.95rem;
            letter-spacing: -0.01em;
        }}

        .status-pill {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            letter-spacing: 0.05em;
        }}

        .status-pill.passed {{
            background-color: var(--pass-bg);
            color: var(--pass-color);
        }}

        .status-pill.failed {{
            background-color: var(--fail-bg);
            color: var(--fail-color);
        }}

        .arrow {{
            font-size: 0.85rem;
            color: var(--text-muted);
            transition: transform 0.2s;
        }}

        .case-card.active .arrow {{
            transform: rotate(180deg);
        }}

        .case-body {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.2s ease-out;
            padding: 0 1.5rem;
        }}

        .case-card.active .case-body {{
            max-height: 3000px;
            padding-bottom: 2rem;
            border-top: 1px solid var(--border-color);
        }}

        /* Two-panel Grid Layout */
        .case-grid {{
            display: grid;
            grid-template-columns: 1.4fr 1fr;
            gap: 2rem;
            margin-top: 1.5rem;
        }}

        @media (max-width: 900px) {{
            .case-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .case-grid-left {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .code-container {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            background-color: var(--code-bg);
        }}

        .code-header {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
            padding: 0.5rem 1rem;
            border-bottom: 1px solid var(--border-color);
            background-color: var(--card-bg);
        }}

        .code-display {{
            font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
            font-size: 0.85rem;
            padding: 1rem;
            overflow-x: auto;
            white-space: pre-wrap;
            color: var(--text-color);
        }}

        .code-display.output-pre {{
            color: var(--text-color);
        }}

        .rules-section {{
            display: flex;
            flex-direction: column;
            height: 100%;
        }}

        .rules-header {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
            padding-bottom: 0.25rem;
        }}

        /* Clean Rules Table */
        .checks-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}

        .checks-table th, .checks-table td {{
            padding: 0.65rem 0.5rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}

        .checks-table th {{
            font-weight: 500;
            color: var(--text-muted);
            font-size: 0.75rem;
            text-transform: uppercase;
        }}

        .check-pass td.check-status-badge {{
            color: var(--pass-color);
            font-weight: 700;
        }}

        .check-fail td.check-status-badge {{
            color: var(--fail-color);
            font-weight: 700;
        }}

        .no-checks {{
            color: var(--text-muted);
            font-style: italic;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-section">
                <span class="logo-title">PromptWatch</span>
                <span class="suite-badge">{html.escape(report.suite_name)}</span>
            </div>
            <button class="theme-toggle" onclick="toggleTheme()">Toggle Theme</button>
        </header>

        <section class="dashboard">
            <div class="widget">
                <h3>Pass Rate</h3>
                <div class="widget-val {status_class}-text">{pass_rate:.1f}%</div>
            </div>
            <div class="widget">
                <h3>Total</h3>
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
                <input type="text" placeholder="Search Case ID..." onkeyup="searchCases(this.value)">
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
                
                old_lines = old_output.splitlines()
                new_lines = new_output.splitlines()
                
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
                <div class="case-header-left">
                    <span class="status-indicator {case_status}"></span>
                    <span class="case-title">{html.escape(case_id)}</span>
                </div>
                <div class="case-header-right">
                    <span class="status-pill {case_status}">{badge_text}</span>
                    <span class="arrow">&#9662;</span>
                </div>
            </div>
            <div class="case-body">
                {diff_html}
            </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptWatch Comparison</title>
    <style>
        :root {{
            --bg-color: #09090b;
            --card-bg: #18181b;
            --card-hover-border: #27272a;
            --text-color: #fafafa;
            --text-muted: #a1a1aa;
            --border-color: #27272a;
            
            --pass-color: #10b981;
            --pass-bg: rgba(16, 185, 129, 0.1);
            --fail-color: #ef4444;
            --fail-bg: rgba(239, 68, 68, 0.1);
            
            --identical-color: #71717a;
            --identical-bg: rgba(113, 113, 122, 0.1);
            --changed-color: #f59e0b;
            --changed-bg: rgba(245, 158, 11, 0.15);
            --added-color: #10b981;
            --added-bg: rgba(16, 185, 129, 0.15);
            --removed-color: #ef4444;
            --removed-bg: rgba(239, 68, 68, 0.15);
            
            --primary-color: #3f3f46;
            --primary-hover: #52525b;
            --accent-color: #ffffff;
            
            --code-bg: #09090b;
        }}
        
        [data-theme="light"] {{
            --bg-color: #fafafa;
            --card-bg: #ffffff;
            --card-hover-border: #e4e4e7;
            --text-color: #09090b;
            --text-muted: #71717a;
            --border-color: #e4e4e7;
            --code-bg: #f4f4f5;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 3rem 1.5rem;
            transition: background-color 0.2s, color 0.2s;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .logo-section {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .logo-title {{
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: var(--text-color);
        }}

        .theme-toggle {{
            background: none;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: background-color 0.2s;
        }}

        .theme-toggle:hover {{
            background-color: var(--card-bg);
        }}

        /* Dashboard grid */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            border: 1px solid var(--border-color);
            background-color: var(--card-bg);
            border-radius: 8px;
            margin-bottom: 3rem;
            overflow: hidden;
        }}

        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        .widget {{
            padding: 2rem 1.5rem;
            text-align: left;
            border-right: 1px solid var(--border-color);
        }}

        .widget:last-child {{
            border-right: none;
        }}

        .widget h3 {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}

        .widget-val {{
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.025em;
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
            gap: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }}

        .filter-tabs {{
            display: flex;
            gap: 0.35rem;
            background-color: var(--card-bg);
            padding: 0.25rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .tab-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 0.4rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .tab-btn:hover {{
            color: var(--text-color);
        }}

        .tab-btn.active {{
            background-color: var(--bg-color);
            color: var(--text-color);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        .search-bar {{
            flex-grow: 1;
            max-width: 350px;
        }}

        .search-bar input {{
            width: 100%;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.55rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            transition: all 0.2s;
        }}

        .search-bar input:focus {{
            outline: none;
            border-color: var(--accent-color);
        }}

        /* Case list */
        .case-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .case-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            transition: border-color 0.2s;
        }}

        .case-card:hover {{
            border-color: var(--card-hover-border);
        }}

        .case-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.25rem 1.5rem;
            cursor: pointer;
            user-select: none;
        }}

        .case-header-left {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .case-header-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .status-indicator {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}

        .status-indicator.identical {{
            background-color: var(--identical-color);
        }}
        .status-indicator.changed {{
            background-color: var(--changed-color);
        }}
        .status-indicator.added {{
            background-color: var(--added-color);
        }}
        .status-indicator.removed {{
            background-color: var(--removed-color);
        }}

        .case-title {{
            font-weight: 600;
            font-size: 0.95rem;
            letter-spacing: -0.01em;
        }}

        .status-pill {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            letter-spacing: 0.05em;
        }}

        .status-pill.identical {{
            background-color: var(--identical-bg);
            color: var(--identical-color);
        }}
        .status-pill.changed {{
            background-color: var(--changed-bg);
            color: var(--changed-color);
        }}
        .status-pill.added {{
            background-color: var(--added-bg);
            color: var(--added-color);
        }}
        .status-pill.removed {{
            background-color: var(--removed-bg);
            color: var(--removed-color);
        }}

        .arrow {{
            font-size: 0.85rem;
            color: var(--text-muted);
            transition: transform 0.2s;
        }}

        .case-card.active .arrow {{
            transform: rotate(180deg);
        }}

        .case-body {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.2s ease-out;
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
            font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
            font-size: 0.85rem;
            padding: 1rem;
            background-color: var(--code-bg);
            border-radius: 8px;
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
            <div class="logo-section">
                <span class="logo-title">PromptWatch Comparison</span>
            </div>
            <button class="theme-toggle" onclick="toggleTheme()">Toggle Theme</button>
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
                <input type="text" placeholder="Search Case ID..." onkeyup="searchCases(this.value)">
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
