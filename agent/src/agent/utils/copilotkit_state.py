
from copilotkit.langgraph import copilotkit_emit_state 
import os

async def emit_state(state, config):
    disable_emit = os.getenv("DISABLE_EMIT_STATE", "false").lower() == "true"
    if not disable_emit:
        return await copilotkit_emit_state(config, state)