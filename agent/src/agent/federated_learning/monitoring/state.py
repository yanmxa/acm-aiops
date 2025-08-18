"""
State management and progress tracking for workflow execution
"""

from typing import Annotated, Sequence, TypedDict, List, Literal
from langchain_core.messages import BaseMessage, RemoveMessage
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

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    progress: List[Node]

# Progress tracking functions

async def complete_node(state: State, node_name: str, message: str, config: RunnableConfig = None) -> None:
    """Update a specific node's completion message with detailed results"""
    if "progress" not in state:
        return
    
    progress = state["progress"]
    display_name = NODE_NAMES.get(node_name, node_name)
    
    # Find the last node with matching name that is not already completed
    target_node = None
    for node in reversed(progress):
        if node["name"] == display_name and node["status"] != "completed":
            target_node = node
            break
    
    if target_node:
        target_node["status"] = "completed"
        target_node["message"] = message
        logger.debug(f"Completed node '{node_name}': {message}")
    else:
        logger.warning(f"No active node '{node_name}' found to complete")
    
    if config:
        await emit_state(state, config)

async def update_node(state: State, node_name: str, status: str, message: str, config: RunnableConfig = None) -> None:
    """Add a new node or update existing node status and message"""
    if "progress" not in state:
        state["progress"] = []
    
    progress = state["progress"]
    display_name = NODE_NAMES.get(node_name, node_name)
    
    # Find the last node with matching name that is not completed
    target_node = None
    for node in reversed(progress):
        if node["name"] == display_name and node["status"] != "completed":
            target_node = node
            break
    
    if target_node:
        # Update existing non-completed node
        target_node["status"] = status
        target_node["message"] = message
    else:
        # Create new node if no non-completed node found
        progress.append({
            "name": display_name,
            "status": status,
            "message": message
        })
    
    logger.info(f"Node '{node_name}' -> {status}: {message}")
    if config:
        await emit_state(state, config)

async def reset_progress(state: State, config: RunnableConfig = None) -> None:
    """Reset progress for a new user query"""
    state["progress"] = []
    logger.debug("Progress reset for new user query")
    
    if config:
        await emit_state(state, config)

async def clear_all_state(state: State, config: RunnableConfig = None) -> State:
    """Clear all messages and progress - for /clear command using RemoveMessage"""
    messages = state.get("messages", [])
    original_count = len(messages)
    
    logger.info(f"Clearing {original_count} messages using RemoveMessage")
    
    # Set progress to show 100% completion for clear operation
    progress = [
        {
            "name": "Clear History",
            "status": "completed",
            "message": f"Cleared {original_count} messages"
        }
    ]
    
    # Use RemoveMessage to delete all existing messages
    # This properly removes them from LangGraph's message store
    if messages:
        remove_messages = [RemoveMessage(id=m.id) for m in messages]
        new_state = {
            "messages": remove_messages,
            "query": "/clear",
            "progress": progress
        }
    else:
        # No messages to remove
        new_state = {
            "messages": [],
            "query": "/clear", 
            "progress": progress
        }
    
    # Emit state to notify frontend of the clear operation
    if config:
        await emit_state(new_state, config)
        logger.info("State emitted after clearing messages")
    
    return new_state
