from typing import Dict, Any, Optional
from core.graph import create_workflow_graph
from core.session_store import SessionStore
from core.state import AgentState, TaskStatus

class WorkflowEngine:
    """
    Main orchestration engine managing the LangGraph state machine,
    Human-in-the-Loop interruptions, and persistent state transitions.
    """
    def __init__(self, session_store: Optional[SessionStore] = None):
        self.graph = create_workflow_graph()
        self.session_store = session_store or SessionStore()

    def start_workflow(self, user_query: str, session_id: str) -> Dict[str, Any]:
        """
        Initializes a new workflow execution run from a user's conversational query.
        """
        initial_state: AgentState = {
            "messages": [{"role": "user", "content": user_query}],
            "user_query": user_query,
            "plan": None,
            "current_task_index": 0,
            "pending_approval_task": None,
            "approval_decision": None,
            "approval_feedback": None,
            "execution_logs": [f"🚀 [Engine] Initialized workflow for query: '{user_query}'"],
            "final_response": None,
            "is_finished": False,
        }
        
        self.session_store.log_audit_event(session_id, "WORKFLOW_STARTED", user_query)
        
        # Run graph until completion or pause at hitl_gate
        final_state = self.graph.invoke(initial_state)
        self.session_store.save_state(session_id, user_query, final_state)
        
        if final_state.get("pending_approval_task"):
            task = final_state["pending_approval_task"]
            self.session_store.log_audit_event(
                session_id, 
                "HITL_APPROVAL_REQUESTED", 
                f"Task {task['id']}: {task['title']} ({task['tool_name']})"
            )
        elif final_state.get("is_finished"):
            self.session_store.log_audit_event(session_id, "WORKFLOW_COMPLETED", "All tasks executed")

        return final_state

    def resume_workflow(self, session_id: str, decision: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Resumes a paused workflow run after user submits approval or rejection.
        """
        saved_state = self.session_store.load_state(session_id)
        if not saved_state:
            raise ValueError(f"No existing workflow session found for id: {session_id}")
            
        pending_task = saved_state.get("pending_approval_task")
        if not pending_task:
            return saved_state

        action_name = "APPROVED" if decision == "approved" else "REJECTED"
        self.session_store.log_audit_event(
            session_id,
            f"USER_{action_name}",
            f"Decision for {pending_task['title']}: {decision} (Feedback: {feedback or 'None'})"
        )
        
        # Update state with user decision
        saved_state["approval_decision"] = decision
        saved_state["approval_feedback"] = feedback
        saved_state["pending_approval_task"] = None
        
        # Resume graph execution from current state
        final_state = self.graph.invoke(saved_state)
        self.session_store.save_state(session_id, saved_state.get("user_query", ""), final_state)
        
        if final_state.get("pending_approval_task"):
            next_task = final_state["pending_approval_task"]
            self.session_store.log_audit_event(
                session_id, 
                "HITL_APPROVAL_REQUESTED", 
                f"Next Task {next_task['id']}: {next_task['title']} ({next_task['tool_name']})"
            )
        elif final_state.get("is_finished"):
            self.session_store.log_audit_event(session_id, "WORKFLOW_COMPLETED", "All tasks resolved")
            
        return final_state
