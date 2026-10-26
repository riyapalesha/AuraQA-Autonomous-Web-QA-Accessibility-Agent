import os
import json
from datetime import datetime
from jinja2 import Template
from playwright.sync_api import sync_playwright
from core.models import PageAuditResult, IssueSeverity
from config import Config

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraQA Audit Report | {{ result.page_title }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f9fafb;
            color: #111827;
            margin: 0;
            padding: 30px 20px;
            line-height: 1.5;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 32px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .header {
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }
        h1 { margin: 0 0 6px 0; font-size: 1.6rem; color: #111827; }
        .meta { color: #6b7280; font-size: 0.9rem; }
        
        .metrics-row {
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
        }
        .metric-card {
            flex: 1;
            padding: 16px;
            border-radius: 6px;
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
            text-align: center;
        }
        .metric-num { font-size: 1.8rem; font-weight: 700; margin: 0; }
        .metric-label { font-size: 0.8rem; color: #4b5563; text-transform: uppercase; font-weight: 600; margin-top: 4px; }
        
        .score-good { color: #15803d; }
        .score-warn { color: #b45309; }
        .score-bad { color: #b91c1c; }

        .summary-box {
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 14px 18px;
            border-radius: 4px;
            margin-bottom: 28px;
            font-size: 0.95rem;
            color: #1e3a8a;
        }

        .issue-card {
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 16px;
            background: #ffffff;
            page-break-inside: avoid;
        }
        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .badge {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
        }
        .badge-p0 { background: #fee2e2; color: #991b1b; }
        .badge-p1 { background: #fef3c7; color: #92400e; }
        .badge-p2 { background: #dbeafe; color: #1e40af; }

        .issue-title { font-size: 1.05rem; font-weight: 600; margin: 0 0 6px 0; color: #111827; }
        .issue-desc { color: #374151; font-size: 0.9rem; margin-bottom: 10px; }
        .code-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 10px 12px;
            font-family: monospace;
            font-size: 0.85rem;
            color: #0f172a;
            white-space: pre-wrap;
            margin-top: 6px;
        }
        footer {
            margin-top: 40px;
            text-align: center;
            color: #9ca3af;
            font-size: 0.85rem;
            border-top: 1px solid #e5e7eb;
            padding-top: 16px;
        }

        @media print {
            body { background: #ffffff; padding: 0; }
            .container { border: none; box-shadow: none; padding: 10px; max-width: 100%; }
            .issue-card { page-break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AuraQA Audit Report: {{ result.page_title }}</h1>
            <div class="meta">
                URL: <strong>{{ result.url }}</strong> &bull; Scanned: {{ result.timestamp }} (Duration: {{ result.duration_seconds }}s)
            </div>
        </div>

        <div class="metrics-row">
            <div class="metric-card">
                <div class="metric-num {% if result.a11y_score >= 80 %}score-good{% elif result.a11y_score >= 60 %}score-warn{% else %}score-bad{% endif %}">
                    {{ result.a11y_score }}/100
                </div>
                <div class="metric-label">Accessibility Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-num score-bad">{{ result.p0_count }}</div>
                <div class="metric-label">Critical Blockers (P0)</div>
            </div>
            <div class="metric-card">
                <div class="metric-num score-warn">{{ result.p1_count }}</div>
                <div class="metric-label">Major Defects (P1)</div>
            </div>
            <div class="metric-card">
                <div class="metric-num">{{ result.total_issues }}</div>
                <div class="metric-label">Total Findings</div>
            </div>
        </div>

        <div class="summary-box">
            <strong>Executive Summary:</strong><br>
            {{ result.hig_summary | replace('\n', '<br>') }}
        </div>

        <h3>Triaged Issues & Recommended Fixes ({{ result.total_issues }})</h3>

        {% if result.issues %}
            {% for issue in result.issues %}
            <div class="issue-card">
                <div class="issue-header">
                    <span class="badge {% if 'P0' in issue.severity.value %}badge-p0{% elif 'P1' in issue.severity.value %}badge-p1{% else %}badge-p2{% endif %}">
                        {{ issue.severity.value }}
                    </span>
                    <small style="color: #6b7280; font-family: monospace;">{{ issue.id }} &bull; {{ issue.category.value }}</small>
                </div>
                <div class="issue-title">{{ issue.title | e }}</div>
                <div class="issue-desc">{{ issue.description | e }}</div>
                
                {% if issue.selector and issue.selector != 'N/A' %}
                <div style="font-size: 0.8rem; color: #4b5563; font-weight: 600;">Affected Selector:</div>
                <div class="code-box" style="margin-bottom: 8px;">{{ issue.selector | e }}</div>
                {% endif %}

                <div style="font-size: 0.8rem; color: #15803d; font-weight: 600;">Recommended Code Fix:</div>
                <div class="code-box" style="background:#f0fdf4; border-color:#bbf7d0; color:#166534;">{{ issue.recommended_fix | e }}</div>
            </div>
            {% endfor %}
        {% else %}
            <p style="color: #15803d;">🎉 No issues found! This page complies with WCAG 2.1 AA standards.</p>
        {% endif %}

        <footer>
            Report generated by AuraQA &mdash; Autonomous Web QA & Accessibility Auditor
        </footer>
    </div>
</body>
</html>
"""

def generate_html_report(result: PageAuditResult, output_filename: str = None) -> str:
    """Renders the PageAuditResult into a clean, simple, printable HTML report."""
    if not output_filename:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"auraqa_report_{timestamp_str}.html"

    filepath = os.path.join(Config.REPORTS_DIR, output_filename)
    template = Template(HTML_TEMPLATE)
    rendered_html = template.render(result=result)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    return filepath

def generate_pdf_report(result: PageAuditResult, output_filename: str = None) -> str:
    """
    Renders the audit report directly into a clean, professional A4 PDF
    using Playwright's headless Chromium print engine.
    """
    if not output_filename:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"auraqa_report_{timestamp_str}.pdf"

    pdf_filepath = os.path.join(Config.REPORTS_DIR, output_filename)
    template = Template(HTML_TEMPLATE)
    rendered_html = template.render(result=result)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(rendered_html, wait_until="load")
        page.pdf(
            path=pdf_filepath,
            format="A4",
            print_background=True,
            margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"}
        )
        browser.close()

    return pdf_filepath
