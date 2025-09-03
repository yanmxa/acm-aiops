"""
Tool Executor - Common logic for executing tools and handling results
"""

import time
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
    
    start_time = time.time()
    logger.debug(f"[PERF] Executing tool '{tool_name}'")
    logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
    
    if tool_name in tool_map:
        try:
            tool = tool_map[tool_name]
            invoke_start = time.time()
            result = await tool.ainvoke(tool_args, config)
            invoke_end = time.time()
            
            logger.debug(f"[PERF] Tool '{tool_name}' completed in {invoke_end - invoke_start:.3f}s")
            
            return ToolMessage(
                content=str(result),
                tool_call_id=tool_call_id,
                name=tool_name
            )
            
        except Exception as e:
            end_time = time.time()
            logger.error(f"[PERF] Tool '{tool_name}' failed after {end_time - start_time:.3f}s: {e}")
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
    """Execute multiple tool calls concurrently and return all result messages"""
    import asyncio
    
    total_start = time.time()
    
    logger.info(f"[PERF] 💫 PARALLEL execution of {len(tool_calls)} tools")
    
    # Create coroutines for all tool calls
    tasks = []
    for i, tool_call in enumerate(tool_calls, 1):
        logger.debug(f"[PERF] Preparing tool {i}/{len(tool_calls)}: {tool_call.get('name', 'unknown')}")
        task = execute_tool_call(tool_call, tool_map, config)
        tasks.append(task)
    
    # Execute all tool calls concurrently
    logger.debug(f"[PERF] Executing {len(tasks)} tools concurrently...")
    tool_messages = await asyncio.gather(*tasks)
    
    total_end = time.time()
    logger.info(f"[PERF] ✨ All {len(tool_calls)} tools completed CONCURRENTLY in {total_end - total_start:.3f}s")
    
    return list(tool_messages)

def count_successful_tools(tool_messages: List[ToolMessage]) -> int:
    """Count the number of successful tool executions"""
    return len([msg for msg in tool_messages 
               if not msg.content.startswith("Error") and not msg.content.startswith("Tool")])