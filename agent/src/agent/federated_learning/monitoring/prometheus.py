
import time
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from agent.federated_learning.monitoring.state import State
from agent.tools.mcp_tool import get_mcp_tools, get_mcp_tools_with_persistent_sessions
from agent.tools.render_recharts import render_recharts
from agent.utils.logging_config import get_logger
from .state import update_node, complete_node
from agent.utils.tool_executor import execute_tool_calls, count_successful_tools

logger = get_logger("prometheus")

async def prometheus_node(state: State, config: RunnableConfig):
    """Simplified tool node for federated monitoring workflow"""
    start_time = time.time()
    logger.info(f"[PERF] ⚡ Prometheus node started")
    
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
    
    # Update progress with all tool names - different messages for different tools
    if "kubectl" in tool_names:
        await update_node(state, "tool", "active", f"Executing kubectl commands: {tool_names_str}", config)
    else:
        await update_node(state, "tool", "active", f"Executing PromQL queries: {tool_names_str}" if tool_names_str else "Executing queries...", config)
    
    # Get available tools
    tools_start = time.time()
    logger.debug(f"[PERF] Starting MCP tools retrieval")
    
    # Use persistent sessions to avoid server restarts
    tools = await get_mcp_tools_with_persistent_sessions()
    tool_map = {tool.name: tool for tool in tools}
    tool_map["render_recharts"] = render_recharts
    
    tools_end = time.time()
    logger.debug(f"[PERF] MCP tools retrieval completed in {tools_end - tools_start:.3f}s ({len(tools)} tools)")
    
    # Execute all tool calls
    exec_start = time.time()
    logger.info(f"[PERF] 🚀 Starting {len(last_message.tool_calls)} tool execution(s) in parallel")
    
    tool_messages = await execute_tool_calls(last_message.tool_calls, tool_map, config)
    
    exec_end = time.time()
    logger.info(f"[PERF] ✅ Tool execution completed in {exec_end - exec_start:.3f}s")
    
    
    # Update messages with tool responses
    updated_messages = messages + tool_messages
    
    # Count successful tool executions and metrics details
    successful_tools = count_successful_tools(tool_messages)
    data_points = 0
    total_series = 0
    
    # Calculate actual metrics from Prometheus responses
    for msg in tool_messages:
        if msg.name in ["prom_query", "prom_range"] and not msg.content.startswith("Error"):
            import json
            try:
                # Parse JSON response to count series and data points
                response_data = json.loads(msg.content)
                if response_data.get("status") == "success":
                    result = response_data.get("data", {}).get("result", [])
                    series_count = len(result)
                    total_series += series_count
                    
                    for series in result:
                        if "values" in series:
                            # Range query: count all time series values
                            data_points += len(series["values"])
                        elif "value" in series:
                            # Instant query: count single value
                            data_points += 1
            except (json.JSONDecodeError, KeyError):
                # If parsing fails, fallback to simple counting
                data_points += msg.content.count('"values":') + msg.content.count('"value":')
    
    # Generate completion message based on tool types
    kubectl_tools = [msg for msg in tool_messages if msg.name == "kubectl"]
    
    if kubectl_tools and successful_tools > 0:
        # For kubectl commands, provide more specific completion message
        completion_msg = f"Executed {len(kubectl_tools)} kubectl command(s) successfully"
    elif successful_tools > 0:
        if data_points > 0 and total_series > 0:
            completion_msg = f"Executed {successful_tools} queries, retrieved {total_series} series with {data_points} data points"
        elif data_points > 0:
            completion_msg = f"Executed {successful_tools} queries, retrieved {data_points} data points"
        else:
            completion_msg = f"Executed {successful_tools} queries successfully"
    else:
        completion_msg = "No data retrieved"
    
    await complete_node(state, "tool", completion_msg, config)
    
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"[PERF] 🎯 Prometheus node completed in {total_time:.3f}s")
    
    return {
        **state,
        "messages": updated_messages,
    }