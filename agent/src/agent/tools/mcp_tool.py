import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import Tool
from langchain_mcp_adapters.sessions import Connection
from dotenv import load_dotenv
import nest_asyncio

from agent.utils.logging_config import get_logger

load_dotenv()

logger = get_logger("mcp_tools")


def get_default_server_configs() -> Dict[str, Dict[str, Any]]:
    """Get default server configurations"""
    config = {
        "prometheus": {
            "command": "npx",
            "args": ["prometheus-mcp-server@1.0.1"],
            "transport": "stdio",
            "env": {
                "PROMETHEUS_URL": os.getenv(
                    "PROMETHEUS_URL", "https://localhost:30090"
                ),
                "PROMETHEUS_INSECURE": os.getenv("PROMETHEUS_INSECURE", "true"),
            },
        }
    }
    return config


# Global MCP client instance
_mcp_client: Optional[MultiServerMCPClient] = None
_tools_cache: Optional[List[Tool]] = None


def get_mcp_client(
    server_configs: dict[str, Connection] | None = None
) -> MultiServerMCPClient:
    """Get or create MCP client"""
    global _mcp_client
    if _mcp_client is None or server_configs is not None:
        configs = server_configs or get_default_server_configs()
        _mcp_client = MultiServerMCPClient(configs)
        logger.debug("MCP client created")
    else:
        logger.debug("Using existing MCP client")
    return _mcp_client


# --- Async version ---
async def async_get_mcp_tools(
    server_configs: dict[str, Connection] | None = None, use_cache: bool = True
) -> List[Tool]:
    """Async: Get all MCP tools from configured servers"""
    global _tools_cache

    if _tools_cache is not None and use_cache:
        logger.debug(f"Using cached MCP tools ({len(_tools_cache)} tools)")
        return _tools_cache

    logger.debug("Fetching MCP tools from servers")
    try:
        # Check if this is first connection before setting cache
        is_first_connection = _tools_cache is None
        
        client = get_mcp_client(server_configs)
        tools = await client.get_tools()
        _tools_cache = tools

        logger.debug(f"Connected to MCP servers with {len(tools)} tools")
        
        # Only show tools on first connection
        if is_first_connection:
            print(f"✅ Connected to MCP servers with {len(tools)} tools")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
        return tools

    except Exception as e:
        logger.error(f"Failed to fetch MCP tools: {str(e)}", exc_info=True)
        raise


# --- Sync version ---
def sync_get_mcp_tools(
    server_configs: dict[str, Connection] | None = None, use_cache: bool = True
) -> List[Tool]:
    """Sync: Get all MCP tools from configured servers"""
    logger.debug("sync_get_mcp_tools called")
    
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        logger.debug("Running in async context, applying nest_asyncio")
        nest_asyncio.apply()
        # Create task and run it
        coro = async_get_mcp_tools(server_configs, use_cache)
        task = asyncio.ensure_future(coro)
        return loop.run_until_complete(task)
    except RuntimeError:
        # No running loop, we can use asyncio.run
        logger.debug("No running event loop, using asyncio.run")
        return asyncio.run(async_get_mcp_tools(server_configs, use_cache))

