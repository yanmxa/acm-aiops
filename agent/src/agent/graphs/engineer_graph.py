from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition

from agent.nodes.engineer import engineer_node
from agent.states.agent_state import AgentState
from agent.states.mcp_state import mcp_tool_state
from agent.nodes.tool import tool_node

# Build the graph
builder = StateGraph(AgentState)

# Define nodes
builder.add_node("tools", tool_node)
builder.add_node("engineer", engineer_node)
# Add Edge
builder.add_edge("tools", "engineer")
builder.add_conditional_edges("engineer", tools_condition)

builder.set_entry_point("engineer")

engineer_graph = builder.compile(checkpointer=MemorySaver())
