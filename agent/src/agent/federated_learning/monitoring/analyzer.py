"""
Analyzer Node - Analyzes metrics data and provides insights with Recharts visualization
"""

import os
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from .state import State
from agent.utils.logging_config import get_logger
from agent.tools.render_recharts import render_recharts
from agent.utils.print_messages import print_messages
from agent.utils.copilotkit_state import emit_state
from .state import update_node, complete_node

logger = get_logger("analyzer")


async def analyzer_node(state: State, config: RunnableConfig = None):
    logger.info(f"Starting analyzer with #message {len(state['messages'])}")
    
    # Update progress
    await update_node(state, "analyzer", "active", "Analyzing metrics data...", config)
    
    if config:
        await emit_state(state, config)

    system_prompt = ANALYZER_PROMPT.format(
        current_time=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    
    state_messages = state["messages"]
    
    # Find if there's a SystemMessage already in the conversation
    has_system_message = any(isinstance(msg, SystemMessage) for msg in state_messages)
    
    if has_system_message:
        # Use existing messages as-is to preserve tool call/tool message relationships
        messages = list(state_messages)
    else:
        # Safe to add SystemMessage at the beginning only if no tool messages exist
        has_tool_messages = any(hasattr(msg, 'name') and msg.name for msg in state_messages)
        
        if has_tool_messages:
            # Don't add SystemMessage to avoid breaking tool call/tool message pairs
            # Instead, append instructions to the last AI message or use a different approach
            messages = list(state_messages)
            logger.warning("Skipping SystemMessage due to existing tool messages in conversation")
        else:
            # Safe to add SystemMessage at the beginning
            messages = [SystemMessage(content=system_prompt)] + list(state_messages)
    
    # Use render_recharts tool for visualization
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    ai_message = await ChatOpenAI(model=model_name).bind_tools([render_recharts]).ainvoke(messages)
    
    # Add metadata to response
    if hasattr(ai_message, 'additional_kwargs'):
        ai_message.additional_kwargs.update({
            "node": "analyzer",
            "model": model_name
        })
    else:
        ai_message.additional_kwargs = {
            "node": "analyzer", 
            "model": model_name
        }
    messages.append(ai_message)
        
    messages = state["messages"] + [ai_message]
    
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
                
            await complete_node(state, "analyzer", completion_msg, config)
        else:
            # First time through analyzer, creating visualizations
            completion_msg = "Initial analysis completed, creating visualizations"
            await complete_node(state, "analyzer", completion_msg, config)
        
    return {
        **state,
        "messages": messages,
    }


# Legacy function removed - use analyzer_node directly


ANALYZER_PROMPT = """
You are a metrics analyzer specialized in multi-cluster performance analysis.

**Workflow:**
1. Analyze metrics data to understand patterns and resource utilization
2. Use render_recharts tool for data visualizations:
   - Multi-cluster comparisons: horizontal comparison charts
   - Single cluster analysis: time-series or component comparison charts
   - Choose LineChart(time-series) for trends or comparisons, BarChart for instant data or comparisons
   - Include relevant y_axis_keys based on metrics (cpu, memory, battery, power, etc.)
   - Use the proper(human-friendly) units for the y_axis_keys:
      - default memory unit is bytes, you can convert to MiB or GiB 
      - default cpu is cores, you can convert to millicores if needed
      - default energy is joules, you can convert to kJ or MJ if needed
  - **IMPORTANT:** If the metrics span different clusters, compare the related/similar components across these clusters, and show the comparison between clusters! The name should convert to be <cluster_name>:<pod-name>. 
  - If you already should these data in a combined chart, then dont plot them one by one again.
   - Dont plot duplicated data, if the data is already plotted, then dont plot it again.
   - Covert the time into right format if show the time in the x-axis.

**Cluster Context:**
- Hub cluster: cluster_name="local-cluster" 
- Managed clusters: actual cluster names (e.g., "cluster1", "cluster2")

NOTE: After visualizing, provide a summary report based on the metrics data. Don't reference the image link in the summary.

[Current Time: {current_time}]
"""