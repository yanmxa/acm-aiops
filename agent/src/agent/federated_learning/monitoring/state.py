"""
State management and progress tracking for workflow execution
"""

from typing import Annotated, Sequence, TypedDict, List, Literal
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from agent.utils.copilotkit_state import emit_state
from agent.utils.logging_config import get_logger

logger = get_logger("state")

# Node display names for UI
NODE_NAMES = {
    "inspector": "Query Understanding",
    "tool": "Data Fetching", 
    "analyzer": "Analysis",
    "chart": "Visualization"
}

NodeStatus = Literal["pending", "active", "completed", "failed"]

class Node(TypedDict):
    name: str
    status: NodeStatus
    message: str

class Progress(TypedDict):
    nodes: List[Node]

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    progress: Progress

# Progress tracking functions

def _sort_nodes(progress: Progress) -> None:
    """Sort nodes: completed first, then pending, then active"""
    status_order = {"completed": 0, "pending": 1, "active": 2}
    progress["nodes"].sort(key=lambda node: status_order.get(node["status"], 3))

async def complete_node(state: State, node_name: str, message: str, config: RunnableConfig = None) -> None:
    """Update a specific node's completion message with detailed results"""
    if "progress" not in state:
        return
    
    progress = state["progress"]
    display_name = NODE_NAMES.get(node_name, node_name)
    
    for node in progress["nodes"]:
        if node["name"] == display_name:
            node["status"] = "completed"
            node["message"] = message
            logger.debug(f"Completed node '{node_name}': {message}")
            break
    else:
        logger.warning(f"Node '{node_name}' not found")
    
    # Sort nodes after update
    _sort_nodes(progress)
    
    if config:
        await emit_state(state, config)

async def update_node(state: State, node_name: str, status: str, message: str, config: RunnableConfig = None) -> None:
    """Add a new node or update existing node status and message"""
    if "progress" not in state:
        state["progress"] = {"nodes": []}
    
    progress = state["progress"]
    display_name = NODE_NAMES.get(node_name, node_name)
    
    existing_node = None
    for node in progress["nodes"]:
        if node["name"] == display_name:
            existing_node = node
            break
    
    if existing_node:
        existing_node["status"] = status
        existing_node["message"] = message
    else:
        progress["nodes"].append({
            "name": display_name,
            "status": status,
            "message": message
        })
    
    logger.debug(f"Node '{node_name}' -> {status}: {message}")
    
    # Sort nodes after update
    _sort_nodes(progress)
    
    if config:
        await emit_state(state, config)
