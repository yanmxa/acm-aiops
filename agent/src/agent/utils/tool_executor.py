"""
Tool Executor - Common logic for executing tools and handling results
"""

from typing import List, Dict, Any
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from agent.utils.logging_config import get_logger

logger = get_logger("tool_executor")

async def execute_tool_call(tool_call: Dict[str, Any], tool_map: Dict[str, Any], config: RunnableConfig = None) -> ToolMessage:
    """Execute a single tool call and return the result message"""
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})
    tool_call_id = tool_call.get("id", "")
    
    logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
    
    if tool_name in tool_map:
        try:
            tool = tool_map[tool_name]
            result = await tool.ainvoke(tool_args, config)
            
            return ToolMessage(
                content=str(result),
                tool_call_id=tool_call_id,
                name=tool_name
            )
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return ToolMessage(
                content=f"Error executing {tool_name}: {str(e)}",
                tool_call_id=tool_call_id,
                name=tool_name
            )
    else:
        logger.warning(f"Tool '{tool_name}' not found in tool map")
        return ToolMessage(
            content=f"Tool '{tool_name}' not found",
            tool_call_id=tool_call_id,
            name=tool_name
        )

async def execute_tool_calls(tool_calls: List[Dict[str, Any]], tool_map: Dict[str, Any], config: RunnableConfig = None) -> List[ToolMessage]:
    """Execute multiple tool calls and return all result messages"""
    tool_messages = []
    
    for tool_call in tool_calls:
        tool_message = await execute_tool_call(tool_call, tool_map, config)
        tool_messages.append(tool_message)
    
    return tool_messages

def count_successful_tools(tool_messages: List[ToolMessage]) -> int:
    """Count the number of successful tool executions"""
    return len([msg for msg in tool_messages 
               if not msg.content.startswith("Error") and not msg.content.startswith("Tool")])