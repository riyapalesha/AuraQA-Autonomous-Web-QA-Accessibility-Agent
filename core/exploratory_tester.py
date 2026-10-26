import time
from typing import List, Dict, Any
from playwright.sync_api import Page
from core.models import IssueCategory, IssueSeverity

class ExploratoryTester:
    """
    Autonomously probes interactive UI elements, forms, links, and buttons
    to surface runtime defects, dead links, and broken affordances.
    """
    def __init__(self, page: Page):
        self.page = page

    def probe_interactive_elements(self) -> List[Dict[str, Any]]:
        """Scans all buttons and links for dead clicks, missing text, or broken targets."""
        defects = []
        
        # 1. Audit ALL Buttons for Missing Text / Non-accessible labels
        buttons = self.page.query_selector_all("button, [role='button']")
        for idx, btn in enumerate(buttons):
            try:
                text = (btn.inner_text() or "").strip()
                aria_label = btn.get_attribute("aria-label") or ""
                title = btn.get_attribute("title") or ""
                
                if not text and not aria_label and not title:
                    html = btn.evaluate("el => el.outerHTML")
                    defects.append({
                        "id": f"UI-BTN-{idx+1:02d}",
                        "title": f"Interactive button missing accessible label / text (#{idx+1})",
                        "category": IssueCategory.ACCESSIBILITY,
                        "severity": IssueSeverity.P1_MAJOR,
                        "wcag": "WCAG 4.1.2 (Name, Role, Value)",
                        "selector": f"button:nth-of-type({idx+1})",
                        "html": html[:150] if html else "<button>",
                        "description": "Button contains no inner text, aria-label, or title, making it invisible to VoiceOver / screen readers.",
                        "impact": "Blind and visually impaired users cannot determine the function of this button.",
                        "fix": "Add an explicit `aria-label='Action Description'` or visible text to the `<button>`."
                    })
            except Exception:
                continue

        # 2. Audit ALL Links for Placeholder / Dead Hrefs (href='#', empty, javascript:void(0))
        links = self.page.query_selector_all("a")
        dead_link_idx = 1
        for a in links:
            try:
                href = (a.get_attribute("href") or "").strip()
                text = (a.inner_text() or "").strip()
                aria = a.get_attribute("aria-label") or ""
                title = a.get_attribute("title") or ""
                label = text or aria or title or "Unnamed Link"
                html = a.evaluate("el => el.outerHTML")

                # Detect unlinked / placeholder links
                is_dead = href in ["#", "", "javascript:void(0)", "javascript:;", "javascript:void(0);"]
                if is_dead:
                    defects.append({
                        "id": f"DEAD-LINK-{dead_link_idx:02d}",
                        "title": f"Placeholder / Dead Link: '{label}' (href='{href}')",
                        "category": IssueCategory.UI_DEFECT,
                        "severity": IssueSeverity.P1_MAJOR,
                        "wcag": "WCAG 2.4.4 (Link Purpose)",
                        "selector": f"a:has-text('{label[:30]}')",
                        "html": html[:150] if html else "<a>",
                        "description": f"The link '{label}' points to a placeholder ('{href}') rather than a valid URL or destination.",
                        "impact": "Users clicking this link experience unexpected scroll jumps or inactive behavior. Degrades navigation trust.",
                        "fix": f"Replace placeholder href='{href}' with the actual destination URL (e.g. 'https://github.com/username' or 'https://linkedin.com/in/...'), or use a semantic button element if triggering an interactive script action."
                    })
                    dead_link_idx += 1

                # Detect external links opening in new tab without rel='noopener noreferrer'
                target = (a.get_attribute("target") or "").lower()
                rel = (a.get_attribute("rel") or "").lower()
                if target == "_blank" and "noopener" not in rel:
                    defects.append({
                        "id": f"SEC-LINK-{dead_link_idx:02d}",
                        "title": f"Security Risk: External link '{label}' opens in new tab without rel='noopener'",
                        "category": IssueCategory.UI_DEFECT,
                        "severity": IssueSeverity.P2_MINOR,
                        "wcag": "Reverse Tabnabbing Security",
                        "selector": f"a:has-text('{label[:30]}')",
                        "html": html[:150] if html else "<a>",
                        "description": f"Link '{label}' has target='_blank' without rel='noopener noreferrer'.",
                        "impact": "Allows newly opened pages to access window.opener and potentially execute reverse-tabnabbing phishing attacks.",
                        "fix": "Add `rel='noopener noreferrer'` to the `<a>` tag."
                    })
                    dead_link_idx += 1

            except Exception:
                continue

        # 3. Heading Hierarchy Audit (e.g. h1 followed directly by h3, skipping h2)
        headings = self.page.query_selector_all("h1, h2, h3, h4, h5, h6")
        prev_level = 0
        for idx, h in enumerate(headings):
            try:
                tag = h.evaluate("el => el.tagName.toLowerCase()")
                level = int(tag.replace("h", ""))
                text = (h.inner_text() or "").strip()
                if prev_level > 0 and level > prev_level + 1:
                    defects.append({
                        "id": f"A11Y-HEAD-{idx+1:02d}",
                        "title": f"Skipped Heading Level: <{tag}> follows <h{prev_level}> ('{text[:30]}')",
                        "category": IssueCategory.ACCESSIBILITY,
                        "severity": IssueSeverity.P2_MINOR,
                        "wcag": "WCAG 1.3.1 (Info and Relationships)",
                        "selector": tag,
                        "html": f"<{tag}>{text[:40]}</{tag}>",
                        "description": f"Heading hierarchy skips from `<h{prev_level}>` directly to `<{tag}>`.",
                        "impact": "Screen-reader users use headings to construct a mental outline of the page. Skipped levels create navigation confusion.",
                        "fix": f"Change `<{tag}>` to `<h{prev_level + 1}>` to preserve strict hierarchical structure."
                    })
                prev_level = level
            except Exception:
                continue

        return defects
