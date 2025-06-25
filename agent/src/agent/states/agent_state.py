from copilotkit import CopilotKitState
from copilotkit.langgraph import copilotkit_emit_state 
from langchain_core.runnables import RunnableConfig


import os

class AgentState(CopilotKitState):
    next_node: str
    update: str
    # deprecated: https://github.com/CopilotKit/CopilotKit/issues/2051
    patch_action_result: dict 

async def emit_state(state: AgentState, config: RunnableConfig):
    """
    Emit the current state to CopilotKit unless DISABLE_EMIT_STATE is set to 'true'.
    """
    disable_emit = os.getenv("DISABLE_EMIT_STATE", "false").lower() == "true"
    if not disable_emit:
        print("emitting state", state["update"])
        return await copilotkit_emit_state(config, state)