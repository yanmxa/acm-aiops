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
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# CopilotKit imports
from copilotkit import CopilotKitState
from copilotkit.langgraph import copilotkit_customize_config, copilotkit_emit_state, copilotkit_interrupt,copilotkit_exit

# LLM imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.states.agent_state import AgentState,emit_state
from agent.tools.render_recharts import render_recharts

from dotenv import load_dotenv
load_dotenv()

    
from agent.states.mcp_state import mcp_tool_state
from agent.utils.logging_config import get_logger

logger = get_logger("tool_node")

async def handle_tool_call(state: AgentState, config: RunnableConfig, tool_call: dict):
    tool_call_id = tool_call.get("id", "")
    tool_call_name = tool_call.get("name", "")
    args = tool_call.get("args", {})
    
    state["update"] = f"Tool node: starting tool call {tool_call_name}"
    await emit_state(state, config)

    # Safely parse JSON string if needed
    try:
        tool_call_args = args if not isinstance(args, str) else json.loads(args)
    except Exception as e:
        return ToolMessage(
            tool_call_id=tool_call_id,
            name=tool_call_name,
            content=f"Failed to parse args: {e}"
        )

    logger.info(f"Starting with tool call: {tool_call_id}: {tool_call_name} {tool_call_args}")

    if tool_call_name == "render_recharts":
        selected_tool = render_recharts
    else:
        selected_tool = mcp_tool_state.name_tool_map.get(tool_call_name)
        
    if not selected_tool:
        return ToolMessage(
            tool_call_id=tool_call_id,
            name=tool_call_name,
            content=f"Tool '{tool_call_name}' not found"
        )

    modifiedConfig = copilotkit_customize_config(
        config,
        emit_tool_calls=True # False if you want to disable tool call streaming
    )
    tool_output = await selected_tool.ainvoke(tool_call_args, modifiedConfig)
    logger.info(f"Completed tool call: {tool_call_id}: {tool_output}")
    
    state["update"] = f"Tool node: completed tool call {tool_call_name}"
    
    # Deprecated: https://github.com/CopilotKit/CopilotKit/issues/2051
    # if the tool_call_args contains cluster, then the key should be tool_call_name + "-" + cluster, else the key should be tool_call_name
    if "cluster" in tool_call_args:
        state["patch_action_result"][tool_call_name + "-" + tool_call_args["cluster"]] = tool_output
    else:
        state["patch_action_result"][tool_call_name] = tool_output
    await emit_state(state, config)

    return ToolMessage(
        tool_call_id=tool_call_id,
        name=tool_call_name,
        content=str(tool_output),
    )

import asyncio

async def tool_node(state: AgentState, config: RunnableConfig):
    messages = state.get("messages", [])
    ai_message = messages[-1]
    
    # Initialize patch_result if it doesn't exist
    if "patch_action_result" not in state:
        state["patch_action_result"] = {}

    if getattr(ai_message, "tool_calls", []):
        tool_messages = await asyncio.gather(*[
            handle_tool_call(state, config, tc) for tc in ai_message.tool_calls
        ])
        messages.extend(tool_messages)
        
    logger.info(f"Tool node completed: {len(messages)} messages, patch_result keys: {list(state.get('patch_action_result', {}).keys())}")
    
    return {
        **state,
        "messages": messages,
    }