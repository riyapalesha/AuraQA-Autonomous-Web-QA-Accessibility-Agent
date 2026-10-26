from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IssueSeverity(str, Enum):
    P0_CRITICAL = "P0 - Critical"
    P1_MAJOR = "P1 - Major"
    P2_MINOR = "P2 - Minor"
    P3_INFO = "P3 - Info"

class IssueCategory(str, Enum):
    ACCESSIBILITY = "Accessibility (WCAG)"
    CONSOLE_ERROR = "Console / JavaScript Error"
    NETWORK_ERROR = "Network / HTTP Failure"
    FORM_VALIDATION = "Form / Input Edge Case"
    UI_DEFECT = "UI / HIG Compliance"

class AuditIssue(BaseModel):
    id: str = Field(description="Unique issue identifier, e.g. 'A11Y-01'")
    title: str = Field(description="Short concise description of the defect")
    category: IssueCategory = Field(description="Defect category")
    severity: IssueSeverity = Field(description="Triage severity priority")
    wcag_criterion: Optional[str] = Field(default=None, description="WCAG 2.1 guideline, e.g. '1.4.3 Contrast (Minimum)'")
    selector: Optional[str] = Field(default=None, description="CSS selector identifying the DOM element")
    html_snippet: Optional[str] = Field(default=None, description="Relevant HTML snippet")
    description: str = Field(description="Detailed explanation of the failure")
    impact: str = Field(description="User impact, particularly for Assistive Technologies / VoiceOver")
    recommended_fix: str = Field(description="Exact code remediation patch (HTML / CSS / JS)")
    screenshot_path: Optional[str] = Field(default=None, description="Path to captured visual evidence")

class PageAuditResult(BaseModel):
    url: str
    page_title: str
    timestamp: str
    duration_seconds: float
    a11y_score: int = Field(ge=0, le=100, description="Accessibility score out of 100")
    total_issues: int = 0
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    issues: List[AuditIssue] = []
    console_errors: List[str] = []
    failed_requests: List[str] = []
    screenshot_path: Optional[str] = None
    hig_summary: str = Field(description="Executive evaluation against Apple Human Interface Guidelines")
