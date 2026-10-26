import pytest
import os
from core.engine import WorkflowEngine
from core.session_store import SessionStore
from core.state import TaskStatus

@pytest.fixture
def test_db_path(tmp_path):
    return str(tmp_path / "test_sessions.db")

def test_incident_workflow_hitl_cycle(test_db_path):
    store = SessionStore(db_path=test_db_path)
    engine = WorkflowEngine(session_store=store)
    session_id = "test-session-123"
    
    query = "Investigate production 500 error spike in checkout cluster, alert on-call lead, and file Jira ticket"
    
    # 1. Start workflow
    state = engine.start_workflow(user_query=query, session_id=session_id)
    
    # Verify planner ran and decomposed tasks
    assert state["plan"] is not None
    assert len(state["plan"]["tasks"]) == 4
    
    # First 2 tasks are read-only and should be completed
    assert state["plan"]["tasks"][0]["status"] == TaskStatus.COMPLETED
    assert state["plan"]["tasks"][1]["status"] == TaskStatus.COMPLETED
    
    # Step 3 requires approval and should have halted the graph
    assert state["pending_approval_task"] is not None
    assert state["pending_approval_task"]["id"] == "task_3"
    assert state["is_finished"] is False
    
    # 2. Resume with User Approval for Step 3
    state2 = engine.resume_workflow(session_id=session_id, decision="approved")
    
    # Step 3 should now be completed
    assert state2["plan"]["tasks"][2]["status"] == TaskStatus.COMPLETED
    
    # Step 4 also requires approval and should now be pending
    assert state2["pending_approval_task"] is not None
    assert state2["pending_approval_task"]["id"] == "task_4"
    assert state2["is_finished"] is False
    
    # 3. Resume with User Approval for Step 4
    state3 = engine.resume_workflow(session_id=session_id, decision="approved")
    
    # All tasks should now be completed, and graph finished
    assert state3["plan"]["tasks"][3]["status"] == TaskStatus.COMPLETED
    assert state3["is_finished"] is True
    assert state3["final_response"] is not None
    assert "Workflow Execution Summary" in state3["final_response"]
    
    # Verify audit logs in SQLite
    audit_trail = store.get_audit_trail(session_id)
    assert len(audit_trail) >= 4

def test_workflow_rejection_branch(test_db_path):
    store = SessionStore(db_path=test_db_path)
    engine = WorkflowEngine(session_store=store)
    session_id = "test-session-reject"
    
    query = "Onboard new contractor with repo write access"
    
    # Start workflow
    state = engine.start_workflow(user_query=query, session_id=session_id)
    assert state["pending_approval_task"] is not None
    
    # Reject the mutating step
    state_after_reject = engine.resume_workflow(
        session_id=session_id, 
        decision="rejected", 
        feedback="Security policy requires VP approval first"
    )
    
    # The rejected task should be marked REJECTED
    rejected_task = [t for t in state_after_reject["plan"]["tasks"] if t["id"] == "task_2"][0]
    assert rejected_task["status"] == TaskStatus.REJECTED
    assert "Security policy requires VP approval" in rejected_task["output"]
