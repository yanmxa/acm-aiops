from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from typing import Literal, TypedDict
from datetime import datetime, timezone

from copilotkit.langgraph import copilotkit_emit_state 
from copilotkit.langgraph import copilotkit_customize_config

from agent.states.agent_state import AgentState,emit_state
from agent.utils.logging_config import get_logger

logger = get_logger("router")

# Structured output for routing
class Route(BaseModel):
    agent: Literal["inspector", "engineer", "generator"] = Field(None, description="The agent to handle user's question")

# Router node
async def router(state: AgentState, config: RunnableConfig):
    if config is None:
        config = RunnableConfig(recursion_limit=25)
        
    model = ChatOpenAI(model="gpt-4o-mini")
    
    # if state["update"] is None:
    #   state["update"] = "Router: routing the query to the appropriate workflow"
    # else:
    #   state["update"] = f"Router: routing the query to the {state['update']}"
    
    state["update"] = "Router: routing the query to the appropriate workflow"
    await emit_state(state, config)
    
    modifiedConfig = copilotkit_customize_config(
        config,
        emit_messages=False, # if you want to disable message streaming
        emit_tool_calls=True # if you want to disable tool call streaming
    )
    route: Route = await model.with_structured_output(Route).ainvoke(
        [
            SystemMessage(
                content=f"""
                You are a Red Hat Advanced Cluster Management assistant that intelligently routes user input to one of the following agents based on intent:

                1. Inspector – Analyzes Kubernetes metrics to provide insights and diagnostics.
                2. Engineer – Executes kubectl commands to interact with the user's Kubernetes cluster.
                3. Generator – Creates specific Kubernetes resources according to the user's request.

                Current time: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
                """
            ),
            state["messages"][-1],
        ],
        modifiedConfig,
    )
    logger.info(f"choose the agent: {route.agent}")

    state["update"] = f"Router: routing the query to the {route.agent}"
    await emit_state(state, config)
    
    # return Command(goto=route.agent)
    return {
            **state,
            "next_node": route.agent,
        }