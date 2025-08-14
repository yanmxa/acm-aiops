
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from agent.federated_learning.monitoring.state import State
from agent.tools.mcp_tool import sync_get_mcp_tools
from agent.tools.render_recharts import render_recharts
from agent.utils.logging_config import get_logger
from .state import update_node, complete_node
from agent.utils.tool_executor import execute_tool_calls, count_successful_tools

logger = get_logger("prometheus")

async def prometheus_node(state: State, config: RunnableConfig):
    """Simplified tool node for federated monitoring workflow"""
    messages = state.get("messages", [])
    if not messages:
        return state
        
    last_message = messages[-1]
    
    # Check if last message has tool calls
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return state
    
    # Get all tool names for progress update
    tool_names = [tool_call.get("name", "") for tool_call in last_message.tool_calls]
    tool_names_str = ", ".join(tool_names) if tool_names else ""
    
    # Update progress with all tool names
    await update_node(state, "tool", "active", f"Executing PromQL queries: {tool_names_str}" if tool_names_str else "Executing queries...", config)
    
    # Get available tools
    tools = sync_get_mcp_tools()
    tool_map = {tool.name: tool for tool in tools}
    tool_map["render_recharts"] = render_recharts
    
    # Execute all tool calls
    tool_messages = await execute_tool_calls(last_message.tool_calls, tool_map, config)
    
    
    # Update messages with tool responses
    updated_messages = messages + tool_messages
    
    # Count successful tool executions and estimate data points
    successful_tools = count_successful_tools(tool_messages)
    data_points = sum(
        msg.content.count('"values":') + msg.content.count('"value":')
        for msg in tool_messages
        if msg.name in ["prom_query", "prom_range"] and not msg.content.startswith("Error")
    )
    
    # Generate completion message
    if successful_tools > 0:
        completion_msg = (f"Executed {successful_tools} queries, retrieved {data_points} data points" 
                         if data_points > 0 else f"Executed {successful_tools} queries successfully")
    else:
        completion_msg = "No data retrieved"
    
    await complete_node(state, "tool", completion_msg, config)
    
    return {
        **state,
        "messages": updated_messages,
    }