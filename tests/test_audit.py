import os
import pytest
from core.agent import AuraQAAgent
from core.models import IssueSeverity, IssueCategory

def test_local_page_audit():
    test_html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_site.html"))
    file_url = f"file:///{test_html_path.replace(os.sep, '/')}"
    
    agent = AuraQAAgent(headless=True)
    result = agent.audit_url(file_url)

    # Assertions
    assert result is not None
    assert result.a11y_score < 100  # Must catch deliberate violations
    assert result.total_issues > 0

    # Verify specific violations caught
    issue_titles = [i.title.lower() for i in result.issues]
    
    # 1. Missing image alt
    assert any("alt" in t for t in issue_titles)

    # 2. Color contrast failure
    assert any("contrast" in t for t in issue_titles)

    # 3. Accessible button or dead link
    assert any("button" in t or "link" in t for t in issue_titles)

    # 4. Report was generated
    assert result.screenshot_path is not None
    assert os.path.exists(result.screenshot_path)
