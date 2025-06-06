from copilotkit import CopilotKitState
from typing_extensions import TypedDict
from typing import Dict, List, Any, Optional, Literal


class ActionState(TypedDict):
    status: Literal["pending", "completed"] = "pending"
    approval: Literal["y", "n"] = "y"
    name: str
    args: str
    output: str
    
class Progress(TypedDict):
    label: str
    value: float
    
class AgentState(CopilotKitState):
    """
    The state of the agent.
    It inherits from CopilotKitState which provides the basic fields needed by CopilotKit.
    """
    hubKubeconfig: str = ""
    update: str = ""
    actions: List[ActionState] = []
    progress: Progress


from dataclasses import dataclass, field

@dataclass
class ToolData:
    tool_map: Dict[str, Any] = field(default_factory=dict)
    tools: List[Any] = field(default_factory=list)
    init: bool = False

tool_data = ToolData()