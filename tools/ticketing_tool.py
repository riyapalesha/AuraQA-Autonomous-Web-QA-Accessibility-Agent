import random
from typing import Dict, Any

def create_jira_ticket(title: str, priority: str = "High", project: str = "INFRA", issue_type: str = "Incident", **kwargs) -> str:
    """Creates an incident or task ticket in Jira / Linear. (Mutating Action)"""
    ticket_id = f"{project}-{random.randint(1000, 9999)}"
    return (
        f"Ticket Created in Jira: [{ticket_id}]\n"
        f"- Summary: {title}\n"
        f"- Type: {issue_type}\n"
        f"- Priority: {priority}\n"
        f"- Status: OPEN (Triaged)\n"
        f"- URL: https://jira.internal.enterprise/browse/{ticket_id}"
    )
