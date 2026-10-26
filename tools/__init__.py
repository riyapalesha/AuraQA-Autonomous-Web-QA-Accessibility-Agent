from typing import Dict, Any, Callable
from tools.telemetry_tool import query_telemetry_logs, verify_access_policy
from tools.devops_tool import get_recent_deployments, grant_repo_access
from tools.ticketing_tool import create_jira_ticket
from tools.comms_tool import send_urgent_alert, send_email_notification

TOOL_REGISTRY: Dict[str, Callable] = {
    "query_telemetry_logs": query_telemetry_logs,
    "verify_access_policy": verify_access_policy,
    "get_recent_deployments": get_recent_deployments,
    "grant_repo_access": grant_repo_access,
    "create_jira_ticket": create_jira_ticket,
    "send_urgent_alert": send_urgent_alert,
    "send_email_notification": send_email_notification,
}

MUTATING_TOOLS = {
    "grant_repo_access",
    "create_jira_ticket",
    "send_urgent_alert",
    "send_email_notification",
}

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Executes a registered enterprise tool safely with argument unpacking."""
    if tool_name not in TOOL_REGISTRY:
        return f"Error: Tool '{tool_name}' not recognized in enterprise registry."
    
    try:
        func = TOOL_REGISTRY[tool_name]
        return func(**arguments)
    except Exception as e:
        return f"Execution Error in '{tool_name}': {str(e)}"
