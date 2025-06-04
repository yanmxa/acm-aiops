"""
A LangGraph implementation of the human-in-the-loop agent.
"""

import json
from typing import Dict, List, Any

# LangGraph imports
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver

# CopilotKit imports
from copilotkit import CopilotKitState
from copilotkit.langgraph import copilotkit_customize_config, copilotkit_emit_state, copilotkit_interrupt,copilotkit_exit

# LLM imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.agent.nodes.agent_state import AgentState

from src.agent.nodes.acm_node import ChatNode
from src.agent.nodes.tool_node import ToolNode

from dotenv import load_dotenv
load_dotenv()

def route_tools(
    state: AgentState,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tool_node"
    return "end_flow"

async def start_flow(state: Dict[str, Any], config: RunnableConfig):
    """
    This is the entry point for the flow.
    """
    # # Initialize steps list if not exists
    # print(f"acm node start: {config["metadata"]["thread_id"]}")
    # print(state)
    
    return Command(
        goto="acm_node",
        update={
            **state,
        }
    )
    
async def end_flow(state: Dict[str, Any], config: RunnableConfig):
    """
    This is the entry point for the flow.
    """
    if "steps" not in state:
        state["steps"] = []
    
    await copilotkit_exit(config)
    return Command(
        goto=END,
        update={
            **state
        }
    )

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("start_flow", start_flow)
workflow.add_node("chat_node", ChatNode)
workflow.add_node("tool_node", ToolNode)
workflow.add_node("end_flow", end_flow)

# Add edges
# workflow.set_entry_point("start_flow")
workflow.add_edge(START, "start_flow")
workflow.add_edge("start_flow", "chat_node")

workflow.add_conditional_edges(
    "chat_node",
    route_tools,
    {"tool_node": "tool_node", "end_flow": "end_flow"},
)

workflow.add_edge("tool_node", "chat_node")
workflow.add_edge("end_flow", END)

# Compile the graph
human_in_the_loop_graph = workflow.compile(checkpointer=MemorySaver())