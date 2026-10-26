from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from core.state import AgentState, TaskStatus, TaskItem
from tools import execute_tool, MUTATING_TOOLS
from config import get_llm

def planner_node(state: AgentState) -> Dict[str, Any]:
    """Analyzes the user's conversational intent and synthesizes an executable DAG plan."""
    # If resuming with an existing plan, preserve state and continue execution
    if state.get("plan") and state.get("plan", {}).get("tasks"):
        return {
            "plan": state["plan"],
            "current_task_index": state.get("current_task_index", 0),
            "pending_approval_task": None,
            "approval_decision": state.get("approval_decision"),
            "approval_feedback": state.get("approval_feedback"),
            "execution_logs": state.get("execution_logs", []),
            "is_finished": state.get("is_finished", False),
        }

    llm = get_llm()
    user_query = state.get("user_query", "")
    
    plan_obj = llm.plan_workflow(user_query)
    plan_dict = plan_obj.model_dump()
    
    log_entry = f"🎯 [Planner] Decomposed request into {len(plan_dict['tasks'])} workflow tasks. Goal: {plan_dict['goal']}"
    
    return {
        "plan": plan_dict,
        "current_task_index": 0,
        "pending_approval_task": None,
        "approval_decision": None,
        "approval_feedback": None,
        "execution_logs": state.get("execution_logs", []) + [log_entry],
        "is_finished": False,
    }

def route_next_step(state: AgentState) -> Literal["synthesizer", "hitl_gate", "executor", "skip_task"]:
    """Conditional router determining whether to execute, seek human approval, or finalize."""
    plan = state.get("plan")
    if not plan or not plan.get("tasks"):
        return "synthesizer"
    
    current_idx = state.get("current_task_index", 0)
    tasks = plan["tasks"]
    
    if current_idx >= len(tasks):
        return "synthesizer"
    
    current_task = tasks[current_idx]
    requires_approval = current_task.get("requires_approval", False) or (current_task.get("tool_name") in MUTATING_TOOLS)
    
    decision = state.get("approval_decision")
    
    if requires_approval:
        if decision == "approved":
            return "executor"
        elif decision == "rejected":
            return "skip_task"
        else:
            # Human-in-the-Loop approval required
            return "hitl_gate"
    
    # Read-only or safe tasks execute automatically
    return "executor"

def hitl_gate_node(state: AgentState) -> Dict[str, Any]:
    """Pauses graph execution to wait for user approval on sensitive/mutating tasks."""
    plan = state.get("plan", {})
    current_idx = state.get("current_task_index", 0)
    current_task = plan["tasks"][current_idx]
    
    current_task["status"] = TaskStatus.REQUIRES_APPROVAL
    log_entry = f"⏸️ [HITL Gate] Paused for human approval on '{current_task['title']}' (Tool: {current_task['tool_name']})"
    
    return {
        "pending_approval_task": current_task,
        "plan": plan,
        "execution_logs": state.get("execution_logs", []) + [log_entry]
    }

def executor_node(state: AgentState) -> Dict[str, Any]:
    """Executes the approved or safe task via the tool registry."""
    plan = state.get("plan", {})
    current_idx = state.get("current_task_index", 0)
    current_task = plan["tasks"][current_idx]
    
    tool_name = current_task["tool_name"]
    arguments = current_task.get("arguments", {})
    
    log_entry = f"⚡ [Executor] Executing step {current_idx + 1}: '{current_task['title']}' using tool '{tool_name}'..."
    output = execute_tool(tool_name, arguments)
    
    current_task["status"] = TaskStatus.COMPLETED
    current_task["output"] = output
    
    result_log = f"✅ [Success] Completed '{current_task['title']}'"
    
    return {
        "plan": plan,
        "current_task_index": current_idx + 1,
        "pending_approval_task": None,
        "approval_decision": None,
        "execution_logs": state.get("execution_logs", []) + [log_entry, result_log]
    }

def skip_task_node(state: AgentState) -> Dict[str, Any]:
    """Handles user rejection of a sensitive step."""
    plan = state.get("plan", {})
    current_idx = state.get("current_task_index", 0)
    current_task = plan["tasks"][current_idx]
    
    feedback = state.get("approval_feedback", "User rejected execution.")
    current_task["status"] = TaskStatus.REJECTED
    current_task["output"] = f"Rejected: {feedback}"
    
    log_entry = f"❌ [Skipped] User rejected '{current_task['title']}'. Reason: {feedback}"
    
    return {
        "plan": plan,
        "current_task_index": current_idx + 1,
        "pending_approval_task": None,
        "approval_decision": None,
        "execution_logs": state.get("execution_logs", []) + [log_entry]
    }

def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    """Synthesizes final summary and closes the workflow session."""
    llm = get_llm()
    plan_dict = state.get("plan", {})
    logs = state.get("execution_logs", [])
    user_query = state.get("user_query", "")
    
    from core.state import WorkflowPlan
    plan_obj = WorkflowPlan(**plan_dict) if plan_dict else None
    
    if plan_obj:
        final_text = llm.synthesize_response(user_query, plan_obj, logs)
    else:
        final_text = "Workflow execution completed."
        
    return {
        "final_response": final_text,
        "is_finished": True,
        "pending_approval_task": None,
        "execution_logs": logs + ["🏁 [Complete] All workflow stages resolved."]
    }

def create_workflow_graph():
    """Builds and compiles the LangGraph state machine with cyclic conditional transitions."""
    workflow = StateGraph(AgentState)
    
    # Register Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("hitl_gate", hitl_gate_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("skip_task", skip_task_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    # Set Entry Point
    workflow.set_entry_point("planner")
    
    # Conditional Routing from Planner
    workflow.add_conditional_edges(
        "planner",
        route_next_step,
        {
            "hitl_gate": "hitl_gate",
            "executor": "executor",
            "synthesizer": "synthesizer",
            "skip_task": "skip_task"
        }
    )
    
    # Conditional Routing from Executor
    workflow.add_conditional_edges(
        "executor",
        route_next_step,
        {
            "hitl_gate": "hitl_gate",
            "executor": "executor",
            "synthesizer": "synthesizer",
            "skip_task": "skip_task"
        }
    )
    
    # Conditional Routing from Skip Task
    workflow.add_conditional_edges(
        "skip_task",
        route_next_step,
        {
            "hitl_gate": "hitl_gate",
            "executor": "executor",
            "synthesizer": "synthesizer",
            "skip_task": "skip_task"
        }
    )
    
    # HITL Gate reaches END for the current execution tick (yielding control to human user)
    workflow.add_edge("hitl_gate", END)
    
    # Synthesizer reaches END
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()
