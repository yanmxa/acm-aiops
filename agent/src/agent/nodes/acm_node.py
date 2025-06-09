"""
A LangGraph implementation of the human-in-the-loop agent.
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime, timezone

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
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama.llms import OllamaLLM

from .agent_state import AgentState
from .agent_state import tool_data  # shared globals
import os 

from dotenv import load_dotenv
load_dotenv()



async def init_resource():  
    client = MultiServerMCPClient({
        "multicluster-mcp-server": {
            "command": "uvx",
            "args": ["multicluster-mcp-server@latest"],
            "transport": "stdio",
            "env": dict(os.environ),
        },
    })
    if not tool_data.init:
        # state["progress"]["label"] = "Chat Node is retrieving available tools..."
        # state["progress"]["value"] = 30
        # await copilotkit_emit_state(config, state)
        tools = await client.get_tools()
        print("init resources")
        for tool in tools:
            print(tool.name)
        tool_data.tools = tools
        tool_map = {tool.name: tool for tool in tools}
        tool_data.tool_map = tool_map
        tool_data.init = True

import asyncio
def schedule_init():
    global init_task
    loop = asyncio.get_event_loop()
    init_task = loop.create_task(init_resource())

schedule_init()

async def ChatNode(state: AgentState, config: RunnableConfig):
    current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    system_prompt = f"""
    You are a Red Hat Advanced Cluster Management assistant that can perform task. current time: {current_timestamp}
    """
    print(f"========================== acm node start: {config["metadata"]["thread_id"]}===================== \n")
    print(state)
    # state["actions"] = []
    # await copilotkit_emit_state(config, state)
    
    # Define the model
    # model = OllamaLLM(model="qwen3:8b")
    model = ChatOpenAI(model="gpt-4o-mini")
    
    
    # clean up the previous actions state to prevent rerender again
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
      state["actions"] = []
    
    if state.get("progress") is None:
        state["progress"] = {"label": "", "value": 0.0}
        
    state["progress"]["label"] = "Chat Node is starting..."
    state["progress"]["value"] = 10
    await copilotkit_emit_state(config, state)
    
    # Define config for the model
    if config is None:
        config = RunnableConfig(recursion_limit=25)
    

    
    # Bind the tools to the model
    model_with_tools = model.bind_tools(
      tool_data.tools,
      # Disable parallel tool calls to avoid race conditions
      parallel_tool_calls=False,
    )

    state["progress"]["label"] = "Chat Node is thinking..."
    state["progress"]["value"] = 50
    await copilotkit_emit_state(config, state)
    # Run the model and generate a response
    response = await model_with_tools.ainvoke([
        SystemMessage(content=system_prompt),
        *state["messages"],
    ], config)

    messages = state["messages"] + [response]
    
    state["messages"] = messages
    state["progress"]["label"] = "Chat Node has generated the result."
    state["progress"]["value"] = 100
    await copilotkit_emit_state(config, state)
    
    print(f"--- acm node end ---: \n {response}")
    
    return {
         **state,
        "messages": messages,
    }