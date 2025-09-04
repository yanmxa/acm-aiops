"""
Inspector Node - Generates PromQL queries based on user queries
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from langchain_core.runnables import RunnableConfig        
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from .state import State
from agent.tools.mcp_tool import get_mcp_tools
from agent.utils.logging_config import get_logger
from agent.utils.model_factory import create_llm
from .state import update_node, complete_node, reset_progress, clear_all_state
from agent.utils.session_config import log_session_activity, get_session_info

logger = get_logger("inspector")

async def inspector_node(state: State, config: RunnableConfig = None) -> State:
    logger.debug("=== Inspector node starting ===")
    logger.info(f"Inspector Input state has {len(state.get('messages', []))} messages")
    
    # Log session activity
    if config:
        log_session_activity(config, "Starting inspector node", "inspector")

    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages in state")

    last_message = messages[-1]
    
    # If last message is HumanMessage, it's a new user query - reset progress
    user_query = ""
    if isinstance(last_message, HumanMessage) and hasattr(last_message, "content"):
        user_query = last_message.content
        
        # Handle /clear command
        if user_query.strip() == "/clear":
            logger.info("Processing /clear command")
            # Clear messages and progress completely
            await reset_progress(state, config)
            # Return completely new state to bypass add_messages
            state = await clear_all_state(state, config)
            
            return {
              **state,
            }
        
        # Reset progress for new user query
        await reset_progress(state, config)
    
    # Update progress
    await update_node(state, "inspector", "active", "Understanding user query...", config)
    
    try:
        tools = await get_mcp_tools()
        include_tools = ["prom_query", "prom_range", "prom_discover", "prom_metadata", "prom_targets", "kubectl"]
        tools = [tool for tool in tools if tool.name in include_tools]
        logger.debug(f"Retrieved {len(tools)} MCP tools")

        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        llm = create_llm(model_name=model_name, temperature=0.1, streaming=True)
        llm = llm.bind_tools(tools)

        utc_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.info(f"Inspector in the current time[UTC]: {utc_time}")


        system_prompt = INSPECTOR_PROMPT.format(
          current_time=utc_time, 
          federated_learning_prompt=FEDERATED_LEARNING_PROMPT,
        )
        
        # Trim messages to stay within token limit (10000 tokens max)
        trimmed_messages = trim_messages(
            messages,
            strategy="last",
            token_counter=count_tokens_approximately,
            max_tokens=10000,
            start_on="human",
            end_on=("human", "tool"),
        )
        
        logger.debug(f"Trimmed messages from {len(messages)} to {len(trimmed_messages)}")
        
        # Send trimmed messages to LLM with system prompt
        response = llm.invoke(
            [SystemMessage(content=system_prompt), *trimmed_messages]
        )
        
        # Add metadata to response
        if hasattr(response, 'additional_kwargs'):
            response.additional_kwargs.update({
                "node": "inspector",
                "model": model_name
            })
        else:
            response.additional_kwargs = {
                "node": "inspector", 
                "model": model_name
            }
        
        # Update completion info based on tool calls made
        if hasattr(response, 'tool_calls') and response.tool_calls:
            prom_calls = []
            kubectl_calls = []
            other_calls = []
            
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                if tool_name in ["prom_query", "prom_range"]:
                    query = tool_call.get("args", {}).get("query", "")
                    if query:
                        prom_calls.append(query)
                elif tool_name == "kubectl":
                    kubectl_calls.append(tool_call)
                else:
                    other_calls.append(tool_name)
            
            # Generate completion message based on what tools were called
            if prom_calls:
                completion_msg = f"PromQL: {', '.join(prom_calls[:2])}" + ("..." if len(prom_calls) > 2 else "")
            elif kubectl_calls:
                completion_msg = f"Generated {len(kubectl_calls)} kubectl command(s)"
            elif other_calls:
                completion_msg = f"Called tools: {', '.join(other_calls)}"
            else:
                completion_msg = "Query analysis completed"
        else:
            completion_msg = "Query analysis completed"
        
        # Update inspector completion immediately
        logger.debug(f"Inspector calling update_node_completion with message: {completion_msg}")
        await complete_node(state, "inspector", completion_msg, config)
        
        if user_query:
            return {
              **state,
              "messages": list(messages) + [response], 
              "query": user_query
              }
        else:
            return {**state,"messages": list(messages) + [response]}

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
   - [Important] Don't generate duplicated queries based on the cluster_name. If user doesn't specify the cluster_name, then you should not set the cluster_name in the query language. Only set the cluster_name if user specify the cluster_name.

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
        * mode="idle": idle energy consumption(filter that)
        * mode="dynamic": dynamic energy consumption under workload(only use this one)
   d) Customized Federated Learning Metrics, like training 'loss', 'accuracy', etc.
      - Each one of the metrics contain the cluster_name, round and pod_name
      - The customized metrics are time series metrics, default get the is the last 7 hours from the current time, and interval is 2 minutes

3. Always preserve the original Prometheus metric metadata and value array in query results.

4. Example tool calls:

Example 1. prom_query - Query the current memory usage of all pods in the hub cluster(local-cluster)
{{
  name: 'prom_query',
  arguments: {{
    query: 'container_memory_usage_bytes{{job="cadvisor", image="", cluster_name="local-cluster"}}'
  }}
}}

Example 2. prom_range - Query the CPU usage of the pod "federated-learning-sample-client-khszf" over the past 1 hour
{{
  name: 'prom_range',
  arguments: {{
    query: 'rate(container_cpu_usage_seconds_total{{job="cadvisor", image="", pod="federated-learning-sample-client-khszf"}}[5m])',
    start: '2025-08-13T08:00:00Z',
    end: '2025-08-13T09:00:00Z',
    step: '1m'
  }}
}}

5. When a user provides a query request, you should:
   - Determine the metric type (memory, cpu, or energy)
   - Generate the correct PromQL query
   - For range queries, ALWAYS use UTC time format in ISO 8601 (e.g., '2025-08-14T10:30:15Z')
   - Call the appropriate tool and return structured results
   - Don't call multiple tools with the similar meaning.

**TOOL CALL RULE**: When calling any tool, do NOT include any content in the message. Only call the tool with parameters - leave message content empty. 

6. Time format guidelines:
   - ALWAYS use UTC time zone for all time calculations
   - For prom_range queries, use UTC timestamps in ISO 8601 format: 'YYYY-MM-DDTHH:MM:SSZ'
   - For relative time periods (e.g., "past 1 hour", "last 30 minutes"):
     * Calculate start time as: current_utc_time - time_period
     * Use current_utc_time as end time
     * NEVER use local time zone - always UTC
   - Examples of correct UTC time calculations:
     * Past 1 hour: start='{current_time}' minus 1 hour, end='{current_time}'
     * Last 30 minutes: start='{current_time}' minus 30 minutes, end='{current_time}'
   
{federated_learning_prompt}
   
[Current Time: {current_time}]
"""

FEDERATED_LEARNING_PROMPT = """
**Federated Learning Operations**

You have two main roles when working with federated learning in the Open Cluster Management environment:

---

### **1. Create/Update/Apply/Delete a Federated Learning instance**

**Use kubectl Tool**: The command and yaml can only have one exists. Use yaml only when you what to update/apply the resource

A federated learning instance is defined by a `FederatedLearning` custom resource.
Example:

```yaml
apiVersion: federation-ai.open-cluster-management.io/v1alpha1
kind: FederatedLearning
metadata:
  name: federated-learning-sample
  namespace: open-cluster-management
spec:
  framework: flower
  server:
    image: <REGISTRY>/flower-app-torch:<IMAGE_TAG>
    rounds: 3
    minAvailableClients: 2
    listeners:
      - name: server-listener
        port: 8080
        type: NodePort
    storage:
      type: PersistentVolumeClaim
      name: model-pvc
      path: /data/models
      size: 2Gi
  client:
    image: <REGISTRY>/flower-app-torch:<IMAGE_TAG>
    placement:
      clusterSets:
        - global
      predicates:
        - requiredClusterSelector:
            claimSelector:
              matchExpressions:
                - key: federated-learning-sample.client-data
                  operator: Exists
```

**Required fields:**

* **Server image** and **client image** (if missing, ask the user).
* **Listener type** for the server.
* **Client placement rules** (e.g., in this example, schedule clients to managed clusters that have the cluster claim `federated-learning-sample.client-data`).

If any of the above information is missing, request it from the user.
Once all required fields are available, use `kubectl(Provide only the 'yaml' input, not both) to create the `FederatedLearning` instance.

---

### **2. Retrieve metrics for a Federated Learning instance**

A federated learning deployment consists of:

* **Server component (pod)** in the hub cluster (`local-cluster`).

  * Pod name format: `<federated-learning-instance-name>-server-*`
  * Example: For the instance `federated-learning-sample`, the hub cluster server pod prefix is `federated-learning-sample-server-*`.

* **Client components (pods)** in the managed clusters.

  * Pod name format: `<federated-learning-instance-name>-client-*`
  * Example: For the instance `federated-learning-sample`, the client pod prefix in a managed cluster is `federated-learning-sample-client-*`.

* **When a user query involves federated learning metrics:**

* Retrieve metrics for both the **server** (hub cluster) and **clients** (managed clusters).
* Filter metrics using `pod` or `pod_name` labels that match the above naming patterns.

* Sample user query: Get the training metrics 'loss' of the instance "federated-learning-sample"

Analysis:
  - The metrics name is "loss", the user dont specify the time range and interval, so you should use the default value.
  - Should have 2 tool calls, one for the server, one for the client. 

Tool calls:
  - tool call 1:  server pod_name name is federated-learning-sample-server-*, the time range is the last 7 hours, and interval is 2 minutes
  - tool call 2:  client pod_name name is federated-learning-sample-client-*, the time range is the last 7 hours, and interval is 2 minutes
"""