from datetime import datetime, timezone
from typing import Any

import asyncio
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from agent.states.agent_state import AgentState
from agent.states.mcp_state import mcp_tool_state
from agent.utils.logging_config import get_logger

logger = get_logger("inspector")
    
async def inspector_node(state: AgentState):
    logger.info(f"Starting inspector with #message {len(state['messages'])}")

    system_prompt = (
        "You are a Kubernetes inspector capable of retrieving metrics across multiple Kubernetes clusters. "
        "If no specific clusters are mentioned, default to the current cluster."
        "Use the 'prometheus' tool to query metric values. "
        "If the time range is not specified, perform a snapshot query. "
        "For range queries, select an appropriate step to ensure the resulting time series contains no more than 50 data points. "
        
        f"Current time: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}"
    )

    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"]
    ]

    allowed_tool_names = {"connect_cluster", "clusters", "prometheus"}
    tools = [tool for tool in mcp_tool_state.mcp_tools if tool.name in allowed_tool_names]
    
    ai_message = await ChatOpenAI(model="gpt-4o-mini").bind_tools(tools).ainvoke(messages)
    
    messages = state["messages"] + [ai_message]
    
    logger.info(f"Ending inspector with #message {len(messages)}")

    return {
            **state,
            "messages": messages,
        }