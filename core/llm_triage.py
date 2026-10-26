import json
import urllib.request
from typing import List, Dict, Any
from core.models import AuditIssue, IssueSeverity, IssueCategory
from config import Config

class AgenticTriageEngine:
    """
    Agentic reasoning engine that triages detected defects, maps them against
    WCAG 2.1 & Apple Human Interface Guidelines (HIG), and synthesizes code patches.
    """
    def __init__(self):
        self.ollama_available = self._check_ollama()

    def _check_ollama(self) -> bool:
        try:
            req = urllib.request.Request(f"{Config.OLLAMA_BASE_URL}/api/tags", headers={"User-Agent": "AuraQA"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def triage_axe_violations(self, raw_violations: List[Dict[str, Any]]) -> List[AuditIssue]:
        issues = []
        for idx, v in enumerate(raw_violations, 1):
            rule_id = v.get("id", "a11y-rule")
            impact = v.get("impact", "minor")
            help_desc = v.get("help", "Accessibility violation")
            tags = v.get("tags", [])
            
            # Map severity
            if impact == "critical":
                sev = IssueSeverity.P0_CRITICAL
            elif impact == "serious":
                sev = IssueSeverity.P1_MAJOR
            elif impact == "moderate":
                sev = IssueSeverity.P2_MINOR
            else:
                sev = IssueSeverity.P3_INFO

            # Extract affected nodes
            nodes = v.get("nodes", [])
            node_count = len(nodes)
            first_node = nodes[0] if nodes else {}
            
            selectors = [n.get("target", [""])[0] for n in nodes[:3] if n.get("target")]
            selector_str = ", ".join(selectors) + (f" (+{node_count - 3} more)" if node_count > 3 else "")
            
            html = first_node.get("html", "")
            summary = first_node.get("failureSummary", help_desc)

            # Identify WCAG tag
            wcag = [t for t in tags if t.startswith("wcag")]
            wcag_label = f"WCAG {wcag[0].replace('wcag', '')}" if wcag else "WCAG 2.1"

            # Generate smart remediation patch
            fix = self._synthesize_fix(rule_id, html, selectors[0] if selectors else "element")

            issue_title = f"{help_desc} ({rule_id})"
            if node_count > 1:
                issue_title += f" — Affects {node_count} elements"

            issues.append(AuditIssue(
                id=f"A11Y-{idx:02d}",
                title=issue_title,
                category=IssueCategory.ACCESSIBILITY,
                severity=sev,
                wcag_criterion=wcag_label,
                selector=selector_str or "N/A",
                html_snippet=html[:200] if html else None,
                description=f"Found on {node_count} element(s). {summary}",
                impact=f"Violates Apple HIG & {wcag_label}: Degrades accessibility for users relying on VoiceOver, high-contrast, or keyboard navigation.",
                recommended_fix=fix
            ))
        return issues

    def triage_console_errors(self, console_errors: List[str]) -> List[AuditIssue]:
        issues = []
        for idx, err in enumerate(console_errors[:5], 1):
            issues.append(AuditIssue(
                id=f"JS-ERR-{idx:02d}",
                title="Uncaught JavaScript Console Exception",
                category=IssueCategory.CONSOLE_ERROR,
                severity=IssueSeverity.P1_MAJOR,
                wcag_criterion="WCAG 2.1 Robust (4.1)",
                selector="window.console",
                html_snippet=None,
                description=f"Runtime script error detected: {err}",
                impact="Uncaught exceptions can halt DOM event listeners, break interactive workflows, and degrade responsive behavior.",
                recommended_fix="Wrap offending script in try-catch block and verify null-checks on referenced DOM elements."
            ))
        return issues

    def triage_network_failures(self, failed_requests: List[str]) -> List[AuditIssue]:
        issues = []
        for idx, req in enumerate(failed_requests[:5], 1):
            issues.append(AuditIssue(
                id=f"NET-{idx:02d}",
                title="HTTP Network Resource Failure",
                category=IssueCategory.NETWORK_ERROR,
                severity=IssueSeverity.P2_MINOR,
                wcag_criterion="Robustness & Asset Integrity",
                selector="Network",
                html_snippet=None,
                description=f"Resource failed to load: {req}",
                impact="Missing stylesheets, scripts, or media assets can lead to layout shifts and broken UI styling.",
                recommended_fix="Verify endpoint URL, CORS configuration, and ensure asset fallback handling is implemented."
            ))
        return issues

    def _synthesize_fix(self, rule_id: str, html: str, selector: str) -> str:
        """Generates exact code remediation snippet based on rule semantics."""
        if "color-contrast" in rule_id:
            return f"CSS Fix for `{selector}`:\nIncrease contrast ratio to at least 4.5:1. Replace current text color with a darker shade: `color: #1a1a1a;` against light backgrounds."
        elif "image-alt" in rule_id:
            return f"HTML Fix for `{selector}`:\nAdd descriptive alternative text: `<img src='...' alt='Descriptive caption here' />`. If decorative, use `alt='' aria-hidden='true'`."
        elif "button-name" in rule_id or "link-name" in rule_id:
            return f"HTML Fix for `{selector}`:\nAdd an accessible label: `<button aria-label='Submit search query'>...</button>`."
        elif "document-title" in rule_id:
            return "HTML Fix in `<head>`:\nAdd a unique, descriptive page title: `<title>Page Name | Company</title>`."
        elif "html-has-lang" in rule_id:
            return "HTML Fix:\nAdd language attribute to root element: `<html lang='en'>`."
        else:
            return f"Remediation for `{selector}`:\nEnsure semantic HTML structure and adhere to ARIA 1.2 landmark specifications."

    def generate_hig_summary(self, score: int, issues: List[AuditIssue], page_title: str) -> str:
        """Synthesizes high-level Apple Human Interface Guidelines assessment."""
        p0 = sum(1 for i in issues if i.severity == IssueSeverity.P0_CRITICAL)
        p1 = sum(1 for i in issues if i.severity == IssueSeverity.P1_MAJOR)
        
        status = "Passed" if score >= 85 and p0 == 0 else "Requires Remediation"
        
        summary = (
            f"Apple Human Interface Guidelines (HIG) Audit Summary for '{page_title}':\n"
            f"- Compliance Status: {status} (Accessibility Score: {score}/100)\n"
            f"- Critical Blockers (P0): {p0} detected.\n"
            f"- Major UX / Contrast Defects (P1): {p1} detected.\n"
            f"- VoiceOver & Accessibility Evaluation: "
        )
        if p0 > 0:
            summary += "Critical ARIA or interactive naming failures will severely impede VoiceOver users. Prioritize P0 fixes immediately."
        elif p1 > 0:
            summary += "Color contrast or semantic element deficiencies detected. Review contrast ratios for Dynamic Type readability."
        else:
            summary += "Strong baseline adherence to inclusive design principles and legible typography."
            
        return summary
