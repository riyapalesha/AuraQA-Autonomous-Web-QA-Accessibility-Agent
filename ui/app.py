import streamlit as st
import time
import uuid
import json
from typing import Dict, Any

from core.engine import WorkflowEngine
from core.session_store import SessionStore
from core.state import TaskStatus
from config import Config

st.set_page_config(
    page_title="AgentFlow | Enterprise Workflow Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stApp { color: #e0e0e0; }
    .approval-card {
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 2px solid #f59e0b;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.15);
    }
    .task-card {
        background-color: #1a1f2c;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-left: 4px solid #6b7280;
    }
    .task-completed { border-left-color: #10b981; }
    .task-approval { border-left-color: #f59e0b; }
    .task-rejected { border-left-color: #ef4444; }
    .task-running { border-left-color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

# Initialize Session Store & Engine
if "session_store" not in st.session_state:
    st.session_state.session_store = SessionStore()
if "engine" not in st.session_state:
    st.session_state.engine = WorkflowEngine(session_store=st.session_state.session_store)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_state" not in st.session_state:
    st.session_state.current_state = None

session_id = st.session_state.session_id
engine: WorkflowEngine = st.session_state.engine
store: SessionStore = st.session_state.session_store

# Sidebar Configuration
with st.sidebar:
    st.title("⚡ AgentFlow")
    st.caption("Conversational Workflow Orchestrator with Human-in-the-Loop")
    st.divider()

    st.subheader("Session Controls")
    st.code(f"Session ID: {session_id}", language="text")
    if st.button("🔄 Start New Workflow Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.session_state.messages = []
        st.session_state.current_state = None
        st.rerun()

    st.divider()
    st.subheader("Quick Enterprise Scenarios")
    
    preset_1 = "P1 Incident: Checkout cluster 500 error spike, alert on-call lead, and file Jira ticket"
    preset_2 = "Onboard backend engineer Alex Chen with payment repo write access and welcome email"
    
    if st.button("🚨 P1 Incident Triage", use_container_width=True):
        st.session_state.prompt_input = preset_1
    if st.button("👤 Contractor Onboarding", use_container_width=True):
        st.session_state.prompt_input = preset_2

    st.divider()
    st.subheader("📋 Live Audit Trail (SQLite)")
    audit_trail = store.get_audit_trail(session_id)
    if audit_trail:
        for ts, act, detail in audit_trail[-5:]:
            st.caption(f"**{ts.split()[1]}** | `{act}`")
            st.text(detail[:60] + "..." if len(detail) > 60 else detail)
    else:
        st.caption("No audit events recorded yet.")

# Main Interface Layout
col_chat, col_workflow = st.columns([1.2, 1.0], gap="large")

# ----------------- LEFT COLUMN: CHAT & HITL APPROVAL -----------------
with col_chat:
    st.header("💬 Conversational Interface")
    st.caption("Type a workflow objective or pick a scenario from the sidebar.")

    # Render Historical Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Check if there is an active pending approval
    state = st.session_state.current_state
    pending_task = state.get("pending_approval_task") if state else None

    if pending_task:
        # Render Interactive HITL Approval Card
        st.markdown(f"""
        <div class="approval-card">
            <h3 style="color: #f59e0b; margin-top:0;">⚠️ Human-in-the-Loop Approval Required</h3>
            <p>The agent is requesting authorization to execute a mutating enterprise action.</p>
            <p><strong>Task:</strong> {pending_task.get('title')}</p>
            <p><strong>Tool:</strong> <code>{pending_task.get('tool_name')}</code></p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 View Action Payload Details", expanded=True):
            st.json(pending_task.get("arguments", {}))

        col_approve, col_reject = st.columns(2)
        with col_approve:
            if st.button("✅ Approve & Execute", type="primary", use_container_width=True):
                with st.spinner("Executing approved task..."):
                    updated_state = engine.resume_workflow(session_id=session_id, decision="approved")
                    st.session_state.current_state = updated_state
                    
                    # If finished, add synthesizer message
                    if updated_state.get("is_finished"):
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": updated_state.get("final_response", "Workflow completed.")
                        })
                    st.rerun()

        with col_reject:
            reject_reason = st.text_input("Rejection note (optional):", key="reject_note", placeholder="e.g. Scope too broad")
            if st.button("❌ Reject / Skip", type="secondary", use_container_width=True):
                with st.spinner("Skipping task..."):
                    updated_state = engine.resume_workflow(
                        session_id=session_id,
                        decision="rejected",
                        feedback=reject_reason or "User manually rejected action"
                    )
                    st.session_state.current_state = updated_state
                    if updated_state.get("is_finished"):
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": updated_state.get("final_response", "Workflow completed.")
                        })
                    st.rerun()

    # Chat Input (Disabled if currently waiting for approval)
    prompt = st.chat_input(
        placeholder="Enter workflow goal..." if not pending_task else "⚠️ Action required: please approve or reject the pending step above",
        disabled=bool(pending_task)
    )

    # Handle preset clicks or chat inputs
    active_prompt = prompt or st.session_state.pop("prompt_input", None)

    if active_prompt and not pending_task:
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        
        with st.chat_message("user"):
            st.markdown(active_prompt)

        with st.spinner("🤖 Agent analyzing intent and orchestrating workflow DAG..."):
            new_state = engine.start_workflow(user_query=active_prompt, session_id=session_id)
            st.session_state.current_state = new_state
            
            if new_state.get("is_finished"):
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": new_state.get("final_response", "Workflow completed.")
                })
            st.rerun()


# ----------------- RIGHT COLUMN: LIVE DAG & MONITOR -----------------
with col_workflow:
    st.header("📊 Workflow Execution Monitor")
    st.caption("Real-time State Machine & Tool Execution Traces")

    if state and state.get("plan"):
        plan = state["plan"]
        st.info(f"**Goal:** {plan.get('goal')}")
        st.caption(f"🧠 *Reasoning:* {plan.get('reasoning')}")

        st.subheader("Dynamic Task Graph")
        tasks = plan.get("tasks", [])
        
        for idx, task in enumerate(tasks, 1):
            status = task.get("status", TaskStatus.PENDING)
            status_style = "task-card"
            badge = "⏳ Pending"
            
            if status == TaskStatus.COMPLETED:
                status_style += " task-completed"
                badge = "✅ Completed"
            elif status == TaskStatus.REQUIRES_APPROVAL:
                status_style += " task-approval"
                badge = "⏸️ Waiting Approval"
            elif status == TaskStatus.REJECTED:
                status_style += " task-rejected"
                badge = "❌ Rejected"
            elif status == TaskStatus.RUNNING:
                status_style += " task-running"
                badge = "⚡ Running"

            st.markdown(f"""
            <div class="{status_style}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong>Step {idx}: {task.get('title')}</strong>
                    <span><code>{badge}</code></span>
                </div>
                <div style="font-size:0.85em; color:#9ca3af; margin-top:4px;">
                    Tool: <code>{task.get('tool_name')}</code> | Sensitive Mutation: <strong>{'Yes' if task.get('requires_approval') else 'No'}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if task.get("output"):
                with st.expander(f"Output for Step {idx}", expanded=False):
                    st.text(task["output"])

        # Execution Logs Console
        st.subheader("📜 Execution Log Trace")
        logs = state.get("execution_logs", [])
        log_text = "\n".join(logs)
        st.text_area("Console", value=log_text, height=200, disabled=True)

    else:
        st.info("No active workflow. Initiate a request in the chat to see real-time task decomposition and execution.")
