from typing import Annotated, Dict, Any, List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

class TaskStatus:
    PENDING = "pending"
    REQUIRES_APPROVAL = "requires_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskItem(BaseModel):
    id: str = Field(description="Unique task identifier, e.g. 'task_1'")
    title: str = Field(description="Short human-readable task name")
    description: str = Field(description="Detailed explanation of what this step executes")
    tool_name: str = Field(description="The name of the tool to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")
    requires_approval: bool = Field(default=False, description="True if step mutates data, alerts people, or causes external side effects")
    status: str = Field(default=TaskStatus.PENDING, description="Current execution status")
    output: Optional[str] = Field(default=None, description="Output/result returned by the tool")

class WorkflowPlan(BaseModel):
    goal: str = Field(description="Clear summary of the user's objective")
    reasoning: str = Field(description="Agent's chain of thought explaining why this plan was chosen")
    tasks: List[TaskItem] = Field(default_factory=list, description="Ordered list of steps to achieve the goal")

class AgentState(TypedDict):
    """
    State stored across nodes in the LangGraph state machine.
    Serialized and saved into persistent SQLite checkpoints.
    """
    messages: List[Dict[str, Any]]
    user_query: str
    plan: Optional[Dict[str, Any]]
    current_task_index: int
    pending_approval_task: Optional[Dict[str, Any]]
    approval_decision: Optional[str]  # "approved", "rejected", or None
    approval_feedback: Optional[str]  # User feedback if rejected or modified
    execution_logs: List[str]
    final_response: Optional[str]
    is_finished: bool
