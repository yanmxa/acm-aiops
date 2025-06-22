import json

# LangGraph imports
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# CopilotKit imports
from copilotkit import CopilotKitState
from copilotkit.langgraph import copilotkit_customize_config, copilotkit_emit_state, copilotkit_interrupt,copilotkit_exit


from agent.states.agent_state import AgentState
from agent.tools.render_recharts import render_recharts

from dotenv import load_dotenv
load_dotenv()

from agent.utils.logging_config import get_logger

logger = get_logger("rechart_node")

async def handle_tool_call(state: AgentState, config: RunnableConfig, tool_call: dict):
    tool_call_id = tool_call.get("id", "")
    tool_call_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    # Safely parse JSON string if needed
    try:
        tool_call_args = args if not isinstance(args, str) else json.loads(args)
    except Exception as e:
        return ToolMessage(
            tool_call_id=tool_call_id,
            name=tool_call_name,
            content=f"Failed to parse args: {e}"
        )

    logger.info(f"tool call input: {tool_call_id}: {tool_call_name} {tool_call_args}")
    
    if tool_call_name == "render_recharts":
        selected_tool = render_recharts
        
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
    
    tool_output = await render_recharts.ainvoke(tool_call_args, modifiedConfig)
    logger.info(f"tool call output: {tool_call_id}: {tool_output}")
    # agentState["update"] = "Router: starting routing decision"
    # await copilotkit_emit_state(config, state)

    return ToolMessage(
        tool_call_id=tool_call_id,
        name=tool_call_name,
        content=str(tool_output),
    )

import asyncio

async def rechart_node(state: AgentState, config: RunnableConfig):
    messages = state.get("messages", [])
    ai_message = messages[-1]

    if getattr(ai_message, "tool_calls", []):
        tool_messages = await asyncio.gather(*[
            handle_tool_call(state, config, tc) for tc in ai_message.tool_calls
        ])
        messages.extend(tool_messages)
    
    return {
        **state,
        "messages": messages,
    }