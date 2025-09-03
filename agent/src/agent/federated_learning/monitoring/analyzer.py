"""
Analyzer Node - Analyzes metrics data and provides insights with Recharts visualization
"""

import os
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from .state import State
from agent.utils.logging_config import get_logger
from agent.utils.model_factory import create_llm
from agent.tools.render_recharts import render_recharts
from agent.utils.print_messages import print_messages
from agent.utils.copilotkit_state import emit_state
from .state import update_node, complete_node
from agent.utils.session_config import log_session_activity

logger = get_logger("analyzer")


async def analyzer_node(state: State, config: RunnableConfig = None):
    logger.info(f"Starting analyzer with #message {len(state['messages'])}")
    
    # Log session activity
    if config:
        log_session_activity(config, "Starting analyzer node", "analyzer")
      
    if len(state["messages"]) == 0:
        return {
            **state,
        }
    
    await update_node(state, "analyzer", "active", "Analyzing metrics data...", config)


    input_messages = state["messages"]
    last_tool_is_render_recharts = False
    if getattr(input_messages[-1], 'name', None) == "render_recharts":
        last_tool_is_render_recharts = True
        # Case 1: Last tool was render_recharts - analyzer already called, just append to conversation
        logger.info("Appending to existing conversation with render_recharts")  
    else:
        # Case 2: Last tool was not render_recharts - create new system + user + tool_data input
        user_query = state.get("query", "")
    
        prometheus_tool_messages = []
        for msg in reversed(input_messages):
            if not isinstance(msg, ToolMessage):
                break
            prometheus_tool_messages.insert(0, msg)
            
        logger.info(f"Creating new analysis with {len(prometheus_tool_messages)} prometheus tool messages")
        
        tool_data_summary = f"\\n\\nAvailable data from tools: {', '.join(msg.name for msg in prometheus_tool_messages)}" if prometheus_tool_messages else ""
        
        input_messages = [
            HumanMessage(content=f"User Query: {user_query}{tool_data_summary}")
        ]
        for tool_msg in prometheus_tool_messages:
            content = getattr(tool_msg, 'content', None)
            name = getattr(tool_msg, 'name', 'unknown')
            input_messages.append(HumanMessage(content=f"Tool {name} output: {content}" if content else f"Tool {name} was called"))

    
    logger.info(f"Analyzer input: {len(input_messages)} total messages")
    
    # Use render_recharts tool for visualization
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    llm = create_llm(model_name=model_name, temperature=0.1, streaming=True)
    ai_message = await llm.bind_tools([render_recharts]).ainvoke([
      SystemMessage(content=ANALYZER_PROMPT.format(
            current_time=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )), 
      *input_messages])
    
    # Add node and model info for pretty printing
    if not hasattr(ai_message, 'additional_kwargs'):
        ai_message.additional_kwargs = {}
    ai_message.additional_kwargs.update({
        "node": "analyzer",
        "model": model_name
    })
    
    messages = state["messages"] + [ai_message]
    
    logger.info(f"Ending analyzer with #message {len(messages)}")
    
    # If analyzer doesn't call tools (no visualization needed), it means we're done
    if not ai_message.tool_calls:
        if last_tool_is_render_recharts:
            # This is the final summary after chart creation
            # Extract and format summary from AI message content
            summary_content = getattr(ai_message, 'content', '')
            if summary_content:
                first_sentence = summary_content.split('. ')[0]
                summary = first_sentence[:100] + ("..." if len(first_sentence) > 100 else "")
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
        "messages": messages + [ai_message],
    }


ANALYZER_PROMPT = """You are a multi-cluster metrics analyzer. Create visualizations and provide insights.

🚨 **CRITICAL**: When calling tools, NEVER generate message content - leave content empty! 🚨

**CRITICAL RULES:**
1. **NO DUPLICATE CHARTS**: Never create duplicate or redundant charts. If similar data exists, combine it in one chart.
2. **MINIMIZE CHARTS**: Maximum 1-2 charts total. Combine related data in single chart.
3. **CLUSTER PREFIXES**: Add cluster prefixes to pod names for clear identification: `cluster1:pod-name`
4. **DATA STRUCTURE**: 
   - BarChart: `{{'pod': 'cluster:pod-name', 'value': number}}`
   - LineChart: `{{'timestamp': number, 'cluster1:pod1': value1, 'cluster2:pod2': value2}}`
5. **Chart Types**: BarChart for pod comparisons, LineChart for time-series
6. **Units**: Use raw values + scaler (e.g., bytes→MiB: 0.00000095367431640625)

**render_recharts Tool - Required Fields:**
• rechart_data: [data array] - Transform Prometheus data to chart format
• rechart_type: 'LineChart' | 'BarChart'
• x_axis_key: string (e.g., 'timestamp', 'component') 
• y_axis_keys: [strings] - MUST EXACTLY MATCH keys in rechart_data objects
• unit: string (e.g., 'MiB', 'cores', 'kJ')
• scaler: number (conversion factor)
• chart_title: string

**CRITICAL TOOL CALL RULE**: 
- When calling render_recharts, do NOT generate any message content
- Leave the message content completely empty ("")
- Only provide tool parameters in the tool_calls array
- NEVER write explanatory text alongside tool calls

**CRITICAL**: y_axis_keys must be EXACT MATCHES of keys in your rechart_data. Inspect your transformed data first!

**Data Format Examples:**

**Option 1 - Bar Chart (Pod Comparison with Cluster Prefixes):**
{{{{
  'charts': [{{{{
    'rechart_data': [
      {{{{'pod': 'local-cluster:bar-server-l9ww4', 'value': 581467340.8}}}},
      {{{{'pod': 'cluster1:bar-client-fhgd9', 'value': 557235855.36}}}},
      {{{{'pod': 'cluster2:bar-client-zlvk8', 'value': 445532123.45}}}}
    ],
    'rechart_type': 'BarChart',
    'x_axis_key': 'pod',
    'y_axis_keys': ['value'],
    'unit': 'MiB',
    'scaler': 0.00000095367431640625,
    'chart_title': 'Memory Usage by Pod Across Clusters'
  }}}}]
}}}}

**Option 2 - Multi-Line Time Series (TRANSFORM long format to wide format):**
{{{{
  'charts': [{{{{
    'rechart_data': [
      {{{{'timestamp': 1755227795, 'local-cluster:foo-server-vkkdf': 581467340.8, 'cluster1:foo-client-q5pls': 557235855.36, 'cluster2:foo-client-hkc9j': 445532123.45}}}},
      {{{{'timestamp': 1755227855, 'local-cluster:foo-server-vkkdf': 2016808140.8, 'cluster1:foo-client-q5pls': 2007393689.6, 'cluster2:foo-client-hkc9j': 1980123456.7}}}}
    ],
    'rechart_type': 'LineChart',
    'x_axis_key': 'timestamp', 
    'y_axis_keys': ['local-cluster:foo-server-vkkdf', 'cluster1:foo-client-q5pls', 'cluster2:foo-client-hkc9j'],
    'unit': 'MiB',
    'scaler': 0.00000095367431640625,
    'chart_title': 'Memory Usage Over Time: Multi-Cluster Comparison'
  }}}}]
}}}}

**KEY PRINCIPLES**: 
1. **Bar Chart**: Each data point = one pod. Use 'pod' as x-axis, 'value' as y-axis.
2. **Time Series**: Transform long format to wide format. Each timestamp becomes one row with multiple pod columns.
   - Long: [{{'timestamp': T1, 'value': V1, 'pod': 'pod1'}}, {{'timestamp': T1, 'value': V2, 'pod': 'pod2'}}]
   - Wide: [{{'timestamp': T1, 'pod1': V1, 'pod2': V2}}]

**VALIDATION STEPS BEFORE CALLING render_recharts:**
1. Build your rechart_data array first
2. Check the EXACT key names in your data objects  
3. Use ONLY those exact keys for y_axis_keys
4. Ensure x_axis_key also exists in the data

**DEBUG REQUIREMENT**: Before creating charts, ALWAYS inspect your transformed data structure and LIST the exact keys available. For example:

For BarChart:
'Available keys: [pod, value]. Using x_axis_key: pod, y_axis_keys: [value]'

For LineChart:
'Available keys: [timestamp, local-cluster:foo-server-vkkdf, cluster1:foo-client-q5pls, cluster2:foo-client-hkc9j]
Using x_axis_key: timestamp, y_axis_keys: [local-cluster:foo-server-vkkdf, cluster1:foo-client-q5pls, cluster2:foo-client-hkc9j]'

**For the Customized Federated Learning Metrics, like training 'loss', 'accuracy', etc.** 
  - The x_axis_key is the round, the y_axis_keys is the value the metrics
  - For there are multiple value in a round, you should use the first one as the y value
  - If these values are too similar across clusters, you should use the bar chart to visualize the metrics, Each cluster should have a bar, You should try to put all the bar into one chart for comparison
  - If the values are too different across cluster, you should use the line chart to visualize the metrics, Each cluster should have a line, You should try to put all the line into one chart for comparison

**CRITICAL**: For time series with multiple pods, TRANSFORM to wide format where each pod becomes a column!

**Output**: 
1. Call render_recharts tool with EMPTY message content ("")
2. AVOID creating multiple charts showing the same or similar data
3. After tool execution, provide concise insights summary in next message 

[Current Time: {current_time}]"""