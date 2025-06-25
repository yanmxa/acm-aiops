from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from copilotkit.langgraph import copilotkit_emit_state 

from agent.states.agent_state import AgentState,emit_state
from agent.states.mcp_state import mcp_tool_state
from agent.utils.logging_config import get_logger
from agent.utils.print_messages import print_messages

logger = get_logger("engineer")

async def engineer_node(state: AgentState, config: RunnableConfig):
    logger.info(f"Starting engineer with #messages: {len(state["messages"])}")
    system_prompt = (
        "You are a Kubernetes engineer that can execute `kubectl` commands on behalf of the user. "
        "Given a natural language request, translate it into the appropriate `kubectl` command, "
        "run it on the target cluster, and return the command output or any relevant error. "
        "Always aim for accuracy and safety in command execution. "
        f"Current time: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}"
    )
    
    try:
        
        state["update"] = "Engineer node: starting"
        await emit_state(state, config)
        
        allowed_tool_names = {"kubectl", "connect_cluster", "clusters"}
        tools = [tool for tool in mcp_tool_state.mcp_tools if tool.name in allowed_tool_names]

        # Ask the model
        ai_message: AIMessage = await ChatOpenAI(model="gpt-4o-mini").bind_tools(tools).ainvoke([
            SystemMessage(content=system_prompt),
            *state["messages"]
        ])

        messages = state["messages"] + [ai_message]
        logger.info(f"Ending engineer with #message {len(messages)}")
        
        state["update"] = "Engineer node: completed"
        await emit_state(state,config)
        
        # print the message in this session
        if len(ai_message.tool_calls) == 0:
            print_messages(messages)
            
        return {
            **state,
            "messages": messages,
        }

    except Exception as e:
        import traceback
        logger.error("Executor encountered an error")
        traceback.print_exc()
        state["update"] = f"Executor: failed - {str(e)}"
        return state