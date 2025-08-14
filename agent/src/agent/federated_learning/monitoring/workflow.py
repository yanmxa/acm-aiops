"""
Prometheus Monitoring Workflow using LangGraph
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
# from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage

from agent.tools.mcp_tool import sync_get_mcp_tools
from agent.tools.render_recharts import render_recharts
from agent.utils.logging_config import get_logger
from .inspector import inspector_node
from .analyzer import analyzer_node
from .chart import chart_node
from .state import State
from .prometheus import prometheus_node
# Removed unused import: complete_progress

logger = get_logger("workflow")

# Initialize the workflow graph
graph = StateGraph(State)

# ========== NODE DEFINITIONS ==========
# Add all workflow nodes
graph.add_node("inspector", inspector_node)     # Inspects user query and determines data needs
graph.add_node("analyzer", analyzer_node)  # Analyzes metrics and creates visualizations
graph.add_node("chart", chart_node)        # Handles chart rendering with render_recharts
graph.add_node("tool", prometheus_node)    # Executes MCP tools (prometheus queries)

# Set workflow entry point
graph.set_entry_point("inspector")

# ========== EDGE ROUTING FUNCTIONS ==========

def inspector_routing(state: State):
    """Route from inspector: check if tools are needed"""
    logger.debug("=== Routing: Inspector ===")
    messages = state["messages"]
    
    last_message = messages[-1]
    logger.debug(f"Last message type: {type(last_message).__name__}")
    
    # If inspector wants to call tools (prometheus queries)
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "fetch_data"  # Go to tool node to fetch prometheus data
    else:
        return "complete"    # End workflow if no tools needed

def tool_result_routing(state: State):
    """Route from tool node: handle prometheus data results"""
    logger.debug("=== Routing: Tool Results ===")
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, ToolMessage):
        # If we got prometheus data, go to analyzer
        if last_message.name in ["prom_query", "prom_range"]:
            return "analyze_data"  # Go to analyzer with prometheus data
    
    # If tool execution failed or unexpected result, go back to inspector
    return "retry_query"

def analyzer_routing(state: State):
    """Route from analyzer: check if visualization is needed"""
    logger.debug("=== Routing: Analyzer ===")
    messages = state["messages"]
    
    last_message = messages[-1]
    logger.debug(f"Last message type: {type(last_message).__name__}")
    
    # Check if analyzer wants to create visualizations
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            # if tool_call.get("name") == "render_recharts":
            return "create_chart"  # Go to chart node for visualization
    
    # Analysis complete, no visualization needed
    return "complete"

# ========== WORKFLOW EDGES ==========

# Inspector → Tool (fetch prometheus data) or END (complete)
graph.add_conditional_edges(
    "inspector", 
    inspector_routing, 
    {
        "fetch_data": "tool",     # Inspector needs prometheus data
        "complete": END           # Inspector determines no data needed
    }
)

# Tool → Analyzer (with data) or Inspector (retry)
graph.add_conditional_edges(
    "tool", 
    tool_result_routing, 
    {
        "analyze_data": "analyzer",   # Successfully fetched prometheus data
        "retry_query": "inspector"    # Tool execution failed, retry
    }
)

# Analyzer → Chart (create visualization) or END (complete)
graph.add_conditional_edges(
    "analyzer", 
    analyzer_routing, 
    {
        "create_chart": "chart",      # Analyzer wants to create charts
        "complete": END               # Analysis complete, no charts needed
    }
)

# Chart → Analyzer (return with chart for final summary)
graph.add_edge("chart", "analyzer")

# ========== COMPILE WORKFLOW ==========
# Compile the graph with memory for state persistence
federated_monitoring_graph = graph.compile(checkpointer=MemorySaver())
