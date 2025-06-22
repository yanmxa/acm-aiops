import langchain_core.messages
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agent.states.agent_state import AgentState
from agent.nodes.tool import tool_node
from agent.nodes.rechart import rechart_node
from agent.nodes.analyzer import analyzer_node
from agent.nodes.inspector import inspector_node
from langgraph.prebuilt import tools_condition


# Build the graph
builder = StateGraph(AgentState)

# Define nodes
builder.add_node("inspector", inspector_node)
builder.add_node("tools", tool_node)
builder.add_node("analyzer", analyzer_node)
builder.add_node("charts", rechart_node)

# inspector -> tools, analyzer
builder.add_edge("inspector", "tools")
builder.add_conditional_edges(
    "tools",
    lambda state: "analyzer" if state["messages"][-1].name == "prometheus" else "inspector",
    {
        "analyzer": "analyzer",
        "inspector": "inspector"
    }
)

# analyzer -> tools, end
builder.add_conditional_edges(
    "analyzer",
    lambda state: "charts" if getattr(state["messages"][-1], "tool_calls", None) else "end",
     {
        "charts": "charts",
        "end": END,
    }
)
builder.add_edge("charts", "analyzer")

# Compile the graph
builder.set_entry_point("inspector")

inspector_graph = builder.compile(checkpointer=MemorySaver())
