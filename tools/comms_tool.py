from typing import Dict, Any

def send_urgent_alert(channel: str, severity: str, summary: str, **kwargs) -> str:
    """Dispatches high-urgency notifications to Slack / PagerDuty. (Mutating Action)"""
    return (
        f"Alert Successfully Dispatched via PagerDuty & Slack:\n"
        f"- Target Channel: {channel}\n"
        f"- Escalation Level: {severity}\n"
        f"- Payload: {summary}\n"
        f"- On-call responders notified: 2 acknowledged."
    )

def send_email_notification(recipient: str, subject: str, **kwargs) -> str:
    """Sends corporate email briefings. (Mutating Action)"""
    return f"Email dispatched to <{recipient}> with subject '{subject}'. Status: 250 OK (Queued for Delivery)."
