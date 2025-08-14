"""
Progress Manager - Handles workflow progress tracking and updates
"""

from .state import AgentState, WorkflowProgress, NodeInfo
from langchain_core.runnables import RunnableConfig
from agent.utils.copilotkit_state import emit_state

# Define the complete workflow sequence
WORKFLOW_NODES = ["inspector", "tool", "analyzer", "chart"]

# Node display names
NODE_DISPLAY_NAMES = {
    "inspector": "Query Understanding",
    "tool": "Data Fetching", 
    "analyzer": "Analysis",
    "chart": "Visualization"
}

async def update_node_completion(state: AgentState, node_name: str, completion_message: str, config: RunnableConfig = None) -> None:
    """Update a specific node's completion message with detailed results"""
    if "workflow_progress" not in state:
        return
    
    progress = state["workflow_progress"]
    
    # Find and update the specific node
    for node_info in progress["nodes_info"]:
        if node_info["node_name"] == NODE_DISPLAY_NAMES.get(node_name, node_name):
            node_info["node_status"] = "completed"
            node_info["node_message"] = completion_message
            print(f"DEBUG: Updated {node_name} to completed with message: {completion_message}")
            break
    else:
        print(f"DEBUG: Could not find node {node_name} in nodes_info")
    
    if config:
        await emit_state(state, config)

# Removed get_node_message - use add_or_update_node with custom messages instead

async def add_or_update_node(state: AgentState, node_name: str, status: str, message: str, config: RunnableConfig = None) -> None:
    """Add a new node or update existing node status and message"""
    if "workflow_progress" not in state:
        state["workflow_progress"] = {"nodes_info": []}
    
    progress = state["workflow_progress"]
    display_name = NODE_DISPLAY_NAMES.get(node_name, node_name)
    
    # Find existing node or create new one
    existing_node = None
    for node_info in progress["nodes_info"]:
        if node_info["node_name"] == display_name:
            existing_node = node_info
            break
    
    if existing_node:
        existing_node["node_status"] = status
        existing_node["node_message"] = message
    else:
        # Add new node
        progress["nodes_info"].append({
            "node_name": display_name,
            "node_status": status,
            "node_message": message
        })
    
    print(f"DEBUG: {node_name} -> {status}: {message}")
    
    # Update general state message
    state["update"] = f"{display_name}: {message}"
    
    if config:
        await emit_state(state, config)

# Removed complete_progress - use add_or_update_node instead

# Removed get_default_status_message - use add_or_update_node with custom messages instead