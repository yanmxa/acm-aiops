from datetime import datetime, timezone
from typing import Any

import asyncio
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from agent.states.agent_state import AgentState
from agent.states.mcp_state import mcp_tool_state
from agent.utils.logging_config import get_logger
from agent.tools.render_recharts import render_recharts
from agent.utils.print_messages import print_messages
from agent.states.agent_state import emit_state

logger = get_logger("analyzer")
    
async def analyzer_node(state: AgentState, config: RunnableConfig):
    logger.info(f"Starting analyzer with #message {len(state['messages'])}")
    
    state["update"] = "Analyzer node: starting"
    await emit_state(state, config)

    system_prompt = (
        "You are a Kubernetes metrics analyzer responsible for evaluating metrics across multiple Kubernetes clusters. "
        "Use the 'render_recharts' tool to visualize the data (rechart_data) where appropriate. "
        "When visualizing:\n"
        "- If the metrics span multiple clusters, prioritize a horizontal comparison in a single chart.\n"
        "- If a unified chart is not feasible due to scale differences, generate separate charts for each cluster.\n"
        
        "After visualizing, provide a summary report based on the metrics data. Don't reference the image link in the summary."
        
        f"Current time: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}"
    )

    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"],
    ]

    ai_message = await ChatOpenAI(model="gpt-4o").bind_tools([render_recharts]).ainvoke(messages)
    messages.append(ai_message)
        
    messages = state["messages"] + [ai_message]
    
    state["update"] = "Analyzer node: completed"
    await emit_state(state, config)
    
    logger.info(f"Ending analyzer with #message {len(messages)}")
    
    if len(ai_message.tool_calls) == 0:
        print_messages(messages)

    return {
            **state,
            "messages": messages,
        }