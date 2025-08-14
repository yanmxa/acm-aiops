"""
Analyzer Node - Analyzes metrics data and provides insights with Recharts visualization
"""

import asyncio
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from .state import AgentState
from agent.utils.logging_config import get_logger
from agent.tools.render_recharts import render_recharts
from agent.utils.print_messages import print_messages
from agent.utils.copilotkit_state import emit_state
from .progress_manager import add_or_update_node, update_node_completion

logger = get_logger("analyzer")


async def analyzer_node(state: AgentState, config: RunnableConfig = None):
    logger.info(f"Starting analyzer with #message {len(state['messages'])}")
    
    # Update progress
    await add_or_update_node(state, "analyzer", "active", "Analyzing metrics data...", config)
    
    state["update"] = "Analyzer node: starting"
    if config:
        await emit_state(state, config)

    system_prompt = ANALYZER_PROMPT.format(
        current_time=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"],
    ]

    # Use render_recharts tool for visualization
    ai_message = await ChatOpenAI(model="gpt-4o").bind_tools([render_recharts]).ainvoke(messages)
    messages.append(ai_message)
        
    messages = state["messages"] + [ai_message]
    
    state["update"] = "Analyzer node: completed"
    if config:
        await emit_state(state, config)
    
    logger.info(f"Ending analyzer with #message {len(messages)}")
    
    # If analyzer doesn't call tools (no visualization needed), it means we're done
    if len(ai_message.tool_calls) == 0:
        # Check if this is coming back from chart (by looking for chart tool messages in history)
        has_chart_messages = any(
            hasattr(msg, 'name') and msg.name == 'render_recharts' 
            for msg in messages if hasattr(msg, 'name')
        )
        
        if has_chart_messages:
            # This is the final summary after chart creation
            # Extract summary from the AI message content 
            summary_content = ai_message.content if hasattr(ai_message, 'content') else ""
            
            # Create a concise summary (first sentence or up to 100 chars)
            if summary_content:
                summary_sentences = summary_content.split('. ')
                summary = summary_sentences[0][:100] + ("..." if len(summary_sentences[0]) > 100 else "")
                completion_msg = f"Summary: {summary}"
            else:
                completion_msg = "Analysis report completed"
                
            await update_node_completion(state, "analyzer", completion_msg, config)
        else:
            # First time through analyzer, creating visualizations
            completion_msg = "Initial analysis completed, creating visualizations"
            await update_node_completion(state, "analyzer", completion_msg, config)
        
        print_messages(messages)

    return {
        **state,
        "messages": messages,
    }


# Legacy function for backwards compatibility
def analyzer(state: AgentState) -> AgentState:
    """Legacy analyzer function - use analyzer_node for new implementations"""
    return asyncio.run(analyzer_node(state, None))


ANALYZER_PROMPT = """
You are a metrics analyzer specialized in multi-cluster performance analysis.

**Workflow:**
1. Analyze metrics data to understand patterns and resource utilization
2. Use render_recharts tool to create visualizations:
   - Multi-cluster comparisons: horizontal comparison charts
   - Single cluster analysis: time-series or component comparison charts
   - Convert metric values from their default units to human-readable formats: for memory metrics in bytes, use MiB or GiB; for CPU metrics in cores or millicores, use cores (e.g., 0.5 cores instead of 500m); for energy metrics in joules, use J or kJ as appropriate.
   
3. Provide summary insights after visualization

**Cluster Context:**
- Hub cluster: cluster_name="local-cluster" 
- Managed clusters: actual cluster names (e.g., "cluster1", "cluster2")

**Visualization:**
- Always use render_recharts for data visualization
- Choose LineChart for trends, BarChart for comparisons
- Include relevant y_axis_keys based on metrics (cpu, memory, battery, power, etc.)

NOTE: After visualizing, provide a summary report based on the metrics data. Don't reference the image link in the summary.

[Current Time: {current_time}]
"""