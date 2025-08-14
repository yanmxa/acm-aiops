"""
Inspector Node - Generates PromQL queries based on user queries
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from .state import State
from agent.tools.mcp_tool import sync_get_mcp_tools
from agent.utils.logging_config import get_logger
from .state import update_node, complete_node

logger = get_logger("inspector")

async def inspector_node(state: State, config: RunnableConfig = None) -> State:
    logger.debug("=== Inspector node starting ===")
    logger.debug(f"Input state has {len(state.get('messages', []))} messages")
    
    # Update progress
    await update_node(state, "inspector", "active", "Understanding user query and generating PromQL...", config)

    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages in state")

    last_message = messages[-1]
    user_query = ""
    if isinstance(last_message, HumanMessage) and hasattr(last_message, "content"):
        user_query = last_message.content

    try:
        tools = sync_get_mcp_tools()
        logger.debug(f"Retrieved {len(tools)} MCP tools")

        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY"),
            streaming=True,
        ).bind_tools(tools)


        system_prompt = INSPECTOR_PROMPT.format(current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        response = llm.invoke(
            [SystemMessage(content=system_prompt), *messages]
        )
        
        # Update completion info with PromQL queries if any tool calls were made
        if hasattr(response, 'tool_calls') and response.tool_calls:
            queries = []
            for tool_call in response.tool_calls:
                if tool_call.get("name") in ["prom_query", "prom_range"]:
                    query = tool_call.get("args", {}).get("query", "")
                    if query:
                        queries.append(query)
            
            if queries:
                completion_msg = f"PromQL: {', '.join(queries[:2])}" + ("..." if len(queries) > 2 else "")
                # Note: Can't await in sync function, will be handled by workflow
            else:
                completion_msg = "Query analysis completed"
        else:
            completion_msg = "No monitoring data needed"
        
        # Update inspector completion immediately
        logger.debug(f"Inspector calling update_node_completion with message: {completion_msg}")
        await complete_node(state, "inspector", completion_msg, config)
        
        if user_query:
            return {
              **state,
              "messages": [response], 
              "query": user_query
              }
        else:
            return {**state,"messages": [response]}

    except Exception as e:
        logger.error(f"Inspector node failed: {str(e)}", exc_info=True)
        raise

INSPECTOR_PROMPT = """
You are **inspector**, a multi-cluster metrics inspector based on Open Cluster Management.
Your task is to retrieve metrics from multiple clusters using the following tools:

- prom_query: Execute a PromQL instant query
- prom_range: Execute a PromQL range query
- prom_discover: Discover all available metrics
- prom_metadata: Get metric metadata
- prom_targets: Get scrape target information

Instructions:
1. Each metric has a cluster_name attribute:
   - Hub cluster: cluster_name="local-cluster"
   - Managed cluster: cluster_name is the actual cluster name, e.g., "cluster1"

2. Focus on the following metrics:
   a) Memory usage (memory metrics)
      - Metric: container_memory_usage_bytes
      - Condition: job="cadvisor", image="" (pod-level)
      - Includes properties in response: cluster_name, pod, namespace, job, instance
   b) CPU usage (cpu metrics)
      - Metric: container_cpu_usage_seconds_total
      - Condition: job="cadvisor", image="" (pod-level)
      - Includes properties: cluster_name, pod, namespace, job, instance, cpu
   c) Energy consumption (energy metrics)
      - Metric: kepler_container_joules_total
      - Condition: service_name="kepler"
      - Includes properties in response: cluster_name, pod_name, container_name, container_namespace, job, instance
      - Split by mode:
        * mode="idle": idle energy consumption
        * mode="dynamic": dynamic energy consumption under workload

3. Always preserve the original Prometheus metric metadata and value array in query results.

4. Example tool calls:

Example 1. prom_query - Query the current memory usage of all pods in the hub cluster
{{
  name: 'prom_query',
  arguments: {{
    query: 'container_memory_usage_bytes{{job="cadvisor", image="", cluster_name="local-cluster"}}'
  }}
}}

Example 2. prom_range - Query the CPU usage of the pod "federated-learning-sample-client-khszf" in the managed cluster over the past 1 hour
{{
  name: 'prom_range',
  arguments: {{
    query: 'rate(container_cpu_usage_seconds_total{{job="cadvisor", image="", cluster_name="cluster1", pod="federated-learning-sample-client-khszf"}}[5m])',
    start: '2025-08-13T08:00:00Z',
    end: '2025-08-13T09:00:00Z',
    step: '1m'
  }}
}}

5. When a user provides a query request, you should:
   - Identify the target cluster (hub or managed)
   - Determine the metric type (memory, cpu, or energy)
   - Generate the correct PromQL query
   - Call the appropriate tool and return structured results
   
[Current Time: {current_time}]
"""