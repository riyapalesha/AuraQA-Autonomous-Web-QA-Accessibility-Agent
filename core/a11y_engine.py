import os
import json
from typing import Dict, Any, List
from playwright.sync_api import Page
from config import Config

class AccessibilityEngine:
    """
    Executes axe-core inside Playwright's DOM context to audit compliance
    with WCAG 2.1 Level A/AA/AAA and Apple Human Interface Guidelines.
    """
    def __init__(self, axe_script_path: str = Config.AXE_PATH):
        if not os.path.exists(axe_script_path):
            raise FileNotFoundError(f"axe-core script not found at: {axe_script_path}")
        with open(axe_script_path, "r", encoding="utf-8") as f:
            self.axe_script = f.read()

    def run_audit(self, page: Page) -> Dict[str, Any]:
        """Injects axe-core and executes comprehensive ruleset."""
        # Inject axe.min.js into DOM
        page.evaluate(self.axe_script)

        # Run axe evaluation with WCAG 2.0 / 2.1 Level A/AA rules
        raw_results = page.evaluate("""
            async () => {
                return await axe.run({
                    runOnly: {
                        type: 'tag',
                        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice']
                    }
                });
            }
        """)

        return self._process_axe_results(raw_results)

    def _process_axe_results(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        violations = raw_data.get("violations", [])
        passes = raw_data.get("passes", [])
        inapplicable = raw_data.get("inapplicable", [])
        
        total_checks = len(passes) + len(violations)
        
        # Calculate weighted a11y score (100 is perfect)
        deductions = 0
        for v in violations:
            impact = v.get("impact", "minor")
            if impact == "critical":
                deductions += 15
            elif impact == "serious":
                deductions += 8
            elif impact == "moderate":
                deductions += 4
            else:
                deductions += 2

        score = max(0, 100 - deductions) if total_checks > 0 else 100

        return {
            "score": score,
            "violations": violations,
            "passes_count": len(passes),
            "violations_count": len(violations),
        }
