
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from agent.federated_learning.monitoring.state import AgentState
from agent.tools.mcp_tool import sync_get_mcp_tools
from agent.tools.render_recharts import render_recharts
from agent.utils.logging_config import get_logger
from .progress_manager import add_or_update_node, update_node_completion
from agent.utils.copilotkit_state import emit_state

logger = get_logger("tool")

async def tool_node(state: AgentState, config: RunnableConfig):
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
    await add_or_update_node(state, "tool", "active", f"Executing PromQL queries: {tool_names_str}" if tool_names_str else "Executing queries...", config)
    
    # Get available tools
    tools = sync_get_mcp_tools()
    tool_map = {tool.name: tool for tool in tools}
    
    # Add render_recharts tool
    tool_map["render_recharts"] = render_recharts
    
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        tool_call_id = tool_call.get("id", "")
        
        logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
        
        # Find and execute the tool
        if tool_name in tool_map:
            try:
                tool = tool_map[tool_name]
                result = await tool.ainvoke(tool_args, config)
                
                tool_message = ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
                tool_messages.append(tool_message)
                
                # Update patch_action_result and emit state for each tool call
                if "patch_action_result" not in state:
                    state["patch_action_result"] = {}
                state["patch_action_result"][tool_name] = str(result)
                if config:
                    await emit_state(state, config)
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                error_message = ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
                tool_messages.append(error_message)
        else:
            error_message = ToolMessage(
                content=f"Tool '{tool_name}' not found",
                tool_call_id=tool_call_id,
                name=tool_name
            )
            tool_messages.append(error_message)
    
    # Update messages with tool responses
    updated_messages = messages + tool_messages
    
    # Count successful tool executions for completion message
    successful_tools = len([msg for msg in tool_messages if not msg.content.startswith("Error") and not msg.content.startswith("Tool")])
    data_points = 0
    
    # Try to estimate data points from prometheus results
    for msg in tool_messages:
        if msg.name in ["prom_query", "prom_range"] and not msg.content.startswith("Error"):
            # Simple heuristic: count result entries
            import json
            try:
                if "result" in msg.content:
                    data_points += msg.content.count('"values":') + msg.content.count('"value":')
            except:
                pass
    
    # Update tool completion message
    if successful_tools > 0:
        completion_msg = f"Executed {successful_tools} queries, retrieved {data_points} data points" if data_points > 0 else f"Executed {successful_tools} queries successfully"
    else:
        completion_msg = "No data retrieved"
    
    await update_node_completion(state, "tool", completion_msg, config)
    
    return {
        **state,
        "messages": updated_messages,
    }