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
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import ToolNode, tools_condition

from .agent_state import AgentState
from .agent_state import tool_data  # shared globals
import os 

from dotenv import load_dotenv
load_dotenv()

client = MultiServerMCPClient({
    "multicluster-mcp-server": {
        "command": "uvx",
        "args": ["multicluster-mcp-server@latest"],
        "transport": "stdio",
        "env": dict(os.environ),
    },
})

async def ChatNode(state: AgentState, config: RunnableConfig):

    system_prompt = """
    You are a Red Hat Advanced Cluster Management assistant that can perform task.
    """
    print(f"========================== acm node start: {config["metadata"]["thread_id"]}=====================")
    print(state)
    
    state["update"] = "acm node thinking"
    state["actions"] = []
    await copilotkit_emit_state(config, state)
    
    # Define the model
    model = ChatOpenAI(model="gpt-4o-mini")
    
    # Define config for the model
    if config is None:
        config = RunnableConfig(recursion_limit=25)
    
    if not tool_data.init:
        tools = await client.get_tools()
        tool_data.tools = tools
        tool_map = {tool.name: tool for tool in tools}
        tool_data.tool_map = tool_map
    
    # Bind the tools to the model
    model_with_tools = model.bind_tools(
      tools,
      # Disable parallel tool calls to avoid race conditions
      parallel_tool_calls=False,
    )

    # Run the model and generate a response
    response = await model_with_tools.ainvoke([
        SystemMessage(content=system_prompt),
        *state["messages"],
    ], config)

    messages = state["messages"] + [response]
    state["messages"] = messages
    await copilotkit_emit_state(config, state)
    
    print(f"--- acm node end ---: \n {response}")
    
    return {
         **state,
        "messages": messages,
    }