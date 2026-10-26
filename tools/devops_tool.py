from typing import Dict, Any, List

def get_recent_deployments(repo: str = "checkout-api", limit: int = 3, **kwargs) -> str:
    """Queries Git VCS history and CI/CD deployment metadata."""
    commits = [
        {"hash": "7f8b91a", "author": "d.kumar", "time": "25 mins ago", "msg": "perf: Increase max DB pool connections to 120 without idle timeout check"},
        {"hash": "3c41ea9", "author": "s.miller", "time": "2 hours ago", "msg": "feat: Add Apple Pay express checkout button"},
        {"hash": "1b09fd2", "author": "a.chen", "time": "5 hours ago", "msg": "chore: Update dependencies in package.json"}
    ]
    formatted = f"Recent Git Deployments for [{repo}]:\n"
    for c in commits[:limit]:
        formatted += f"- [{c['hash']}] {c['time']} by {c['author']}: '{c['msg']}'\n"
    formatted += "Suspicious commit identified: [7f8b91a] directly correlates with connection pool exhaustion."
    return formatted

def grant_repo_access(repo: str, permission: str, user: str, **kwargs) -> str:
    """Grants GitHub / GitLab repository permissions. (Mutating Action)"""
    return f"Successfully provisioned [{permission}] permissions on repository [{repo}] for user [{user}]."
