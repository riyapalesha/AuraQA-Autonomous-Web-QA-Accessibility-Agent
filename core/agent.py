import time
from datetime import datetime
from typing import Optional, Dict, Any

from config import Config
from core.models import PageAuditResult, IssueSeverity
from core.browser_driver import BrowserSession
from core.a11y_engine import AccessibilityEngine
from core.exploratory_tester import ExploratoryTester
from core.llm_triage import AgenticTriageEngine
from core.report_generator import generate_html_report, generate_pdf_report

class AuraQAAgent:
    """
    Main autonomous QA & Accessibility agent coordinating browser automation,
    DOM/A11y inspection, exploratory testing, LLM triage, and report generation.
    """
    def __init__(self, headless: Optional[bool] = None):
        self.headless = Config.HEADLESS if headless is None else headless
        self.a11y_engine = AccessibilityEngine()
        self.triage_engine = AgenticTriageEngine()

    def audit_url(self, url: str) -> PageAuditResult:
        start_time = time.time()
        session = BrowserSession(headless=self.headless)
        
        try:
            # 1. Launch Browser & Navigate
            page = session.start()
            success, title_or_error = session.navigate(url)
            
            if not success:
                raise RuntimeError(f"Could not load '{url}': {title_or_error}")
            
            page_title = title_or_error or url
            
            # 2. Capture Visual Evidence Screenshot
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"screenshot_{timestamp_str}.png"
            screenshot_path = session.capture_screenshot(screenshot_name)

            # 3. Execute axe-core WCAG Audit
            a11y_raw = self.a11y_engine.run_audit(page)
            a11y_score = a11y_raw.get("score", 100)
            axe_violations = a11y_raw.get("violations", [])

            # 4. Run Exploratory Probing
            tester = ExploratoryTester(page)
            exploratory_defects = tester.probe_interactive_elements()

            # 5. Capture Telemetry (Console Errors & Network Failures)
            console_errors = session.console_errors
            failed_requests = session.failed_requests

        finally:
            # Safely close browser session (in headful mode, add brief pause so users can view the page)
            pause_time = 2.5 if not self.headless else 0.0
            session.close(pause_seconds=pause_time)

        # 6. Agentic Triage & Remediation Synthesis
        triage_issues = []
        
        # A11y Violations
        triage_issues.extend(self.triage_engine.triage_axe_violations(axe_violations))
        
        # Exploratory Defects
        from core.models import AuditIssue
        for d in exploratory_defects:
            triage_issues.append(AuditIssue(
                id=d["id"],
                title=d["title"],
                category=d["category"],
                severity=d["severity"],
                wcag_criterion=d.get("wcag"),
                selector=d.get("selector"),
                html_snippet=d.get("html"),
                description=d["description"],
                impact=d["impact"],
                recommended_fix=d["fix"]
            ))

        # Console & Network Errors
        triage_issues.extend(self.triage_engine.triage_console_errors(console_errors))
        triage_issues.extend(self.triage_engine.triage_network_failures(failed_requests))

        # 7. Compute Severity Breakdown
        p0_count = sum(1 for i in triage_issues if i.severity == IssueSeverity.P0_CRITICAL)
        p1_count = sum(1 for i in triage_issues if i.severity == IssueSeverity.P1_MAJOR)
        p2_count = sum(1 for i in triage_issues if i.severity == IssueSeverity.P2_MINOR)

        duration = round(time.time() - start_time, 2)
        
        # 8. Apple HIG Executive Summary
        hig_summary = self.triage_engine.generate_hig_summary(a11y_score, triage_issues, page_title)

        result = PageAuditResult(
            url=url,
            page_title=page_title,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration_seconds=duration,
            a11y_score=a11y_score,
            total_issues=len(triage_issues),
            p0_count=p0_count,
            p1_count=p1_count,
            p2_count=p2_count,
            issues=triage_issues,
            console_errors=console_errors,
            failed_requests=failed_requests,
            screenshot_path=screenshot_path,
            hig_summary=hig_summary
        )

        # 9. Generate HTML & PDF Reports
        generate_html_report(result)
        generate_pdf_report(result)
        return result
