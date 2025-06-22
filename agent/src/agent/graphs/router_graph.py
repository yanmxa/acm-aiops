from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.nodes.router import router
from agent.nodes.inspector import inspector_node
from agent.states.agent_state import AgentState
from agent.graphs.engineer_graph import engineer_graph
from agent.graphs.inspector_graph import inspector_graph

def mock_generator(state: AgentState):
    return {"output": f"[Generator] Generated resource for input: {state['messages']}"}

# Build the graph
builder = StateGraph(AgentState)

# Define nodes
builder.add_node("router", router)

builder.add_node("inspector_graph", inspector_graph)
builder.add_node("engineer_graph", engineer_graph)
builder.add_node("generator_graph", mock_generator)

# builder.add_edge("router", "inspector")
def route_agent(
    state: AgentState,
):
    next_node = state.get("next_node")
    if next_node == "inspector":
        return "inspector_graph"
    elif next_node == "engineer":
        return "engineer_graph"
    elif next_node == "generator":
        return "generator_graph"
    else:
        raise ValueError(f"Unknown agent: {next_node}")

builder.add_conditional_edges(
    "router",
    route_agent,
    {
        "inspector_graph": "inspector_graph",
        "engineer_graph": "engineer_graph",
        "generator_graph": "generator_graph",
    }
)

builder.set_entry_point("router")

# Compile the graph
router_graph = builder.compile(checkpointer=MemorySaver())
