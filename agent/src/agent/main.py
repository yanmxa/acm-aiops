from fastapi import FastAPI
import asyncio
import uuid
from typing import Dict, List, Any, Optional
import os
import uvicorn
# LangGraph imports
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

# CopilotKit imports
from copilotkit import CopilotKitState, CopilotKitSDK, LangGraphAgent
from copilotkit.langgraph import (
    copilotkit_customize_config
)
from copilotkit.langgraph import (copilotkit_exit)
from copilotkit.integrations.fastapi import add_fastapi_endpoint
# OpenAI imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from src.agent.acm_graph import human_in_the_loop_graph 

app = FastAPI()

sdk = CopilotKitSDK(
    agents=[
        LangGraphAgent(
            name="chat_agent",
            description="An example for showcasing the  AGUI protocol using LangGraph.",
            graph=human_in_the_loop_graph
        ),
    ]
)

add_fastapi_endpoint(app, sdk, "/copilotkit")


@app.get("/")
async def root():
    return {"message": "Hello World!!"}


def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "src.agent.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )

if __name__ == "__main__":
    main()

