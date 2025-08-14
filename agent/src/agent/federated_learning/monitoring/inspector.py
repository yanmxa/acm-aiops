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
from agent.tools.mcp_tool import get_mcp_tools
from agent.utils.logging_config import get_logger
from .state import update_node, complete_node, reset_progress

logger = get_logger("inspector")

async def inspector_node(state: State, config: RunnableConfig = None) -> State:
    logger.debug("=== Inspector node starting ===")
    logger.debug(f"Input state has {len(state.get('messages', []))} messages")

    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages in state")

    last_message = messages[-1]
    
    # If last message is HumanMessage, it's a new user query - reset progress
    user_query = ""
    if isinstance(last_message, HumanMessage) and hasattr(last_message, "content"):
        user_query = last_message.content
        # Reset progress for new user query
        await reset_progress(state, config)
    # else:
    #     # Get the original user query (first HumanMessage)
    #     for msg in messages:
    #         if isinstance(msg, HumanMessage) and hasattr(msg, "content"):
    #             user_query = msg.content
    #             break
    # Update progress
    await update_node(state, "inspector", "active", "Understanding user query...", config)
    
    try:
        tools = await get_mcp_tools()
        include_tools = ["prom_query", "prom_range", "prom_discover", "prom_metadata", "prom_targets", "kubectl"]
        tools = [tool for tool in tools if tool.name in include_tools]
        logger.debug(f"Retrieved {len(tools)} MCP tools")

        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY"),
            streaming=True,
        ).bind_tools(tools)


        system_prompt = INSPECTOR_PROMPT.format(
          current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
          federated_learning_prompt=FEDERATED_LEARNING_PROMPT,
        )
        # Send all messages to LLM with system prompt
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
   
{federated_learning_prompt}
   
[Current Time: {current_time}]
"""

FEDERATED_LEARNING_PROMPT = """
**Federated Learning Operations**

You have two main roles when working with federated learning in the Open Cluster Management environment:

---

### **1. Create a Federated Learning instance**

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

**When a user query involves federated learning metrics:**

* Retrieve metrics for both the **server** (hub cluster) and **clients** (managed clusters).
* Filter metrics using `pod` or `pod_name` labels that match the above naming patterns.

"""