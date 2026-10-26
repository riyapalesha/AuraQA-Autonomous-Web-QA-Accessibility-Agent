import json
from typing import Dict, Any, List
from core.state import WorkflowPlan, TaskItem, TaskStatus

class MockWorkflowLLM:
    """
    Intelligent simulated LLM engine for AgentFlow.
    Generates realistic dynamic DAG workflow plans and reasoning
    even when running offline without external API keys.
    """
    def __init__(self):
        pass

    def plan_workflow(self, user_query: str) -> WorkflowPlan:
        query_lower = user_query.lower()
        
        # Scenario 1: IT Incident / Error Triage
        if any(w in query_lower for w in ["error", "500", "incident", "failure", "crash", "cluster", "checkout", "p1", "down"]):
            return WorkflowPlan(
                goal="Investigate production checkout cluster errors, diagnose root cause, and alert on-call response team",
                reasoning="Identified high-priority system degradation request. Will fetch telemetry logs, cross-reference recent Git commits, draft an RCA, and seek human approval before paging on-call or filing high-priority Jira tickets.",
                tasks=[
                    TaskItem(
                        id="task_1",
                        title="Query Telemetry Logs",
                        description="Fetch error rate, HTTP 500 spike metrics, and recent stack traces from telemetry service",
                        tool_name="query_telemetry_logs",
                        arguments={"service": "checkout-api", "timeframe": "last_1_hour", "level": "ERROR"},
                        requires_approval=False,
                        status=TaskStatus.PENDING
                    ),
                    TaskItem(
                        id="task_2",
                        title="Inspect Git Commit History",
                        description="Examine recent deployment commits to checkout-api service for risky diffs",
                        tool_name="get_recent_deployments",
                        arguments={"repo": "checkout-api", "limit": 3},
                        requires_approval=False,
                        status=TaskStatus.PENDING
                    ),
                    TaskItem(
                        id="task_3",
                        title="Draft & Dispatch On-Call PagerDuty Alert",
                        description="Page the on-call Site Reliability Engineering lead and post in #incidents-war-room",
                        tool_name="send_urgent_alert",
                        arguments={
                            "channel": "#incidents-war-room",
                            "severity": "CRITICAL - P1",
                            "summary": "Checkout API 500 error spike detected following commit 7f8b91 (DB Connection Pool exhaustion)."
                        },
                        requires_approval=True,  # HITL Gate!
                        status=TaskStatus.PENDING
                    ),
                    TaskItem(
                        id="task_4",
                        title="Create High-Priority Jira Incident Ticket",
                        description="File official Jira ticket with reproduction steps, stack traces, and suggested rollback",
                        tool_name="create_jira_ticket",
                        arguments={
                            "project": "INFRA",
                            "issue_type": "Incident",
                            "priority": "Highest",
                            "title": "P1 Incident: Checkout service connection pool leak",
                            "assignee": "sre-oncall"
                        },
                        requires_approval=True,  # HITL Gate!
                        status=TaskStatus.PENDING
                    )
                ]
            )

        # Scenario 2: Employee / User Onboarding & Access Provisioning
        elif any(w in query_lower for w in ["onboard", "access", "employee", "account", "contractor", "permission", "provision"]):
            return WorkflowPlan(
                goal="Onboard engineer, provision access to repositories, and generate welcoming briefing",
                reasoning="Access management workflow detected. Will verify policy constraints, request authorization for repository write access and cloud credentials, and dispatch confirmation upon approval.",
                tasks=[
                    TaskItem(
                        id="task_1",
                        title="Verify Organizational Policy",
                        description="Check role permissions, team assignment, and email alias availability",
                        tool_name="verify_access_policy",
                        arguments={"role": "Backend Engineer", "department": "Platform"},
                        requires_approval=False,
                        status=TaskStatus.PENDING
                    ),
                    TaskItem(
                        id="task_2",
                        title="Provision Repository Access",
                        description="Grant read/write access to production repositories and CI/CD pipelines",
                        tool_name="grant_repo_access",
                        arguments={"repo": "payment-service", "permission": "write", "user": "new-hire"},
                        requires_approval=True,  # HITL Gate!
                        status=TaskStatus.PENDING
                    ),
                    TaskItem(
                        id="task_3",
                        title="Dispatch Welcome Briefing & Calendar Invite",
                        description="Send welcome package and schedule 1-on-1 team introductory sync",
                        tool_name="send_email_notification",
                        arguments={"recipient": "new-hire@company.com", "subject": "Welcome to the Engineering Team!"},
                        requires_approval=False,
                        status=TaskStatus.PENDING
                    )
                ]
            )

        # Default Generic Enterprise Workflow
        else:
            return WorkflowPlan(
                goal=f"Execute automated workflow for: {user_query}",
                reasoning="Synthesized custom workflow DAG. Read operations execute automatically; mutation and dispatch operations pause for human review.",
                tasks=[
                    TaskItem(
                        id="task_1",
                        title="Collect Diagnostic Context",
                        description="Query system state, database records, and relevant environment logs",
                        tool_name="query_telemetry_logs",
                        arguments={"query": user_query},
                        requires_approval=False,
                        status=TaskStatus.PENDING
                    ),
                    TaskItem(
                        id="task_2",
                        title="Execute Action & Apply System Updates",
                        description="Apply the requested workflow operation to the target environment",
                        tool_name="create_jira_ticket",
                        arguments={"title": f"Action Item: {user_query[:40]}", "priority": "Medium"},
                        requires_approval=True,  # HITL Gate!
                        status=TaskStatus.PENDING
                    )
                ]
            )

    def synthesize_response(self, user_query: str, plan: WorkflowPlan, execution_logs: List[str]) -> str:
        completed = [t for t in plan.tasks if t.status == TaskStatus.COMPLETED]
        rejected = [t for t in plan.tasks if t.status == TaskStatus.REJECTED]
        
        res = f"### Workflow Execution Summary\n\n"
        res += f"**Goal:** {plan.goal}\n\n"
        res += f"**Execution Breakdown:**\n"
        res += f"- **Successfully Executed Tasks:** {len(completed)} / {len(plan.tasks)}\n"
        if rejected:
            res += f"- **Rejected / Skipped by User:** {len(rejected)} task(s)\n"
            
        res += "\n**Detailed Results:**\n"
        for t in plan.tasks:
            icon = "✅" if t.status == TaskStatus.COMPLETED else ("❌" if t.status == TaskStatus.REJECTED else "⏸️")
            res += f"- {icon} **{t.title}**: {t.output or 'Skipped/Halted'}\n"
            
        res += "\nAll actions and audit logs have been recorded to the compliance trail."
        return res
