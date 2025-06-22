import os
import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass, field
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool

from dotenv import load_dotenv
load_dotenv()

@dataclass
class McpToolState:
    name_tool_map: Dict[str, BaseTool] = field(default_factory=dict)
    mcp_tools: List[BaseTool] = field(default_factory=list)
    initialized: bool = False

mcp_tool_state = McpToolState()

async def initialize_mcp_tools():
    client = MultiServerMCPClient({
        "multicluster-mcp-server": {
            "command": "npx",
            "args": ["-y", "multicluster-mcp-server@latest"],
            "transport": "stdio",
            "env": dict(os.environ),
        },
    })

    if not mcp_tool_state.initialized:
        tools = await client.get_tools()
        mcp_tool_state.mcp_tools = tools
        mcp_tool_state.name_tool_map = {tool.name: tool for tool in tools}
        mcp_tool_state.initialized = True

        for tool in tools:
            print(tool.name)

def schedule_mcp_tool_initialization():
    asyncio.get_event_loop().create_task(initialize_mcp_tools())

# Trigger initialization on import
schedule_mcp_tool_initialization()
