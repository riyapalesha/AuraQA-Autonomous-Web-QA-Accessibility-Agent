import argparse
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.agent import AuraQAAgent

def main():
    parser = argparse.ArgumentParser(description="AuraQA: Autonomous AI Web QA & Accessibility Auditor")
    parser.add_argument("--url", type=str, required=True, help="Target URL to audit (e.g. https://news.ycombinator.com)")
    parser.add_argument("--headful", action="store_true", help="Launch real visible browser window on screen")
    args = parser.parse_args()

    print("=" * 70)
    print("[AuraQA] Autonomous Web QA & Accessibility Agent")
    print("=" * 70)
    print(f"Target URL: {args.url}")
    print(f"Browser Mode: {'Visible (Headful)' if args.headful else 'Headless'}")
    print("\n[1/5] Initializing Playwright Chromium Engine...")
    
    agent = AuraQAAgent(headless=not args.headful)
    
    print("[2/5] Navigating and Capturing DOM tree...")
    print("[3/5] Injected axe-core: running WCAG 2.1 AA/AAA compliance audit...")
    print("[4/5] Probing interactive elements & evaluating console telemetry...")
    print("[5/5] Synthesizing remediation patches & Apple HIG executive summary...")
    
    try:
        result = agent.audit_url(args.url)
        print("\n" + "=" * 70)
        print(f"AUDIT COMPLETE for '{result.page_title}'")
        print("=" * 70)
        print(f"Accessibility Score: {result.a11y_score}/100")
        print(f"P0 Critical Blockers: {result.p0_count}")
        print(f"P1 Major Defects:     {result.p1_count}")
        print(f"Total Findings:       {result.total_issues}")
        print(f"Duration:             {result.duration_seconds}s")
        print("\nApple HIG Summary:")
        print(result.hig_summary)
        print("\nTop Triaged Issues:")
        for idx, issue in enumerate(result.issues[:5], 1):
            print(f"  {idx}. [{issue.severity.value}] {issue.title} (Selector: {issue.selector})")
            print(f"     Fix: {issue.recommended_fix[:100]}...\n")
        print(f"Report saved to reports/ directory.")
    except Exception as e:
        print(f"\n[ERROR] Audit Execution Failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
