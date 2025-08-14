"""
Chart Node - Handles render_recharts tool calls for visualization
"""

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from agent.federated_learning.monitoring.state import AgentState
from agent.tools.render_recharts import render_recharts
from agent.utils.logging_config import get_logger
from .progress_manager import add_or_update_node, update_node_completion

logger = get_logger("chart")

async def chart_node(state: AgentState, config: RunnableConfig):
    """Handle render_recharts tool calls separately"""
    logger.info(f"Starting chart node with #message {len(state['messages'])}")
    
    # Update progress
    await add_or_update_node(state, "chart", "active", "Generating visualizations...", config)
    
    messages = state.get("messages", [])
    if not messages:
        return state
        
    last_message = messages[-1]
    
    # Check if last message has tool calls
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return state
    
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        tool_call_id = tool_call.get("id", "")
        
        logger.debug(f"Executing chart tool: {tool_name} with args: {tool_args}")
        
        # Only handle render_recharts in this node
        if tool_name == "render_recharts":
            try:
                result = await render_recharts.ainvoke(tool_args, config)
                
                tool_message = ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
                tool_messages.append(tool_message)
                
            except Exception as e:
                logger.error(f"Chart tool execution failed: {e}")
                error_message = ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
                tool_messages.append(error_message)
    
    # Update messages with tool responses
    updated_messages = messages + tool_messages
    
    # Count charts created and get their types
    chart_details = []
    logger.debug(f"DEBUG: Processing {len(tool_messages)} tool messages")
    
    for tool_call, msg in zip(last_message.tool_calls, tool_messages):
        logger.debug(f"DEBUG: tool_call name: {tool_call.get('name')}, msg content: {msg.content[:100]}...")
        
        if tool_call.get("name") == "render_recharts":
            # Check if the tool execution was successful (not an error message)
            is_error = msg.content.startswith("Error") or "error" in msg.content.lower()
            logger.debug(f"DEBUG: render_recharts call - is_error: {is_error}")
            
            if not is_error:
                # Extract chart type from tool call arguments
                charts = tool_call.get("args", {}).get("charts", [])
                logger.debug(f"DEBUG: Found {len(charts)} charts in args")
                
                for chart in charts:
                    chart_type = chart.get("rechart_type", "chart")
                    logger.debug(f"DEBUG: Chart type: {chart_type}")
                    
                    # Convert to more readable format
                    if chart_type == "BarChart":
                        chart_details.append("bar chart")
                    elif chart_type == "LineChart":
                        chart_details.append("line chart")
                    else:
                        chart_details.append("chart")
    
    # Update chart completion message
    logger.debug(f"DEBUG: chart_details = {chart_details}")
    
    if chart_details:
        if len(chart_details) == 1:
            completion_msg = f"Generated 1 {chart_details[0]}"
        else:
            # Group by type and count
            from collections import Counter
            type_counts = Counter(chart_details)
            parts = []
            for chart_type, count in type_counts.items():
                if count == 1:
                    parts.append(f"1 {chart_type}")
                else:
                    parts.append(f"{count} {chart_type}s")
            completion_msg = f"Generated {', '.join(parts)}"
    else:
        # Fallback: check if we have any successful render_recharts calls
        successful_calls = len([msg for msg in tool_messages 
                              if msg.name == "render_recharts" and not msg.content.startswith("Error")])
        
        if successful_calls > 0:
            completion_msg = f"Generated {successful_calls} chart{'s' if successful_calls > 1 else ''}"
            logger.debug(f"DEBUG: Using fallback detection - {successful_calls} successful calls")
        else:
            completion_msg = "No visualizations created"
    
    logger.debug(f"DEBUG: Final completion_msg = {completion_msg}")
    await update_node_completion(state, "chart", completion_msg, config)
    
    logger.info(f"Ending chart node with #message {len(updated_messages)}")
    
    return {
        **state,
        "messages": updated_messages,
    }