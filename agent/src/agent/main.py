from fastapi import FastAPI
import os
import uvicorn

# CopilotKit imports
from copilotkit import  CopilotKitSDK, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint

# from agent.graphs.router_graph import router_graph
from agent.federated_learning.monitoring.workflow import federated_monitoring_graph
from agent.utils.session_config import create_session_config
from agent.utils.logging_config import get_logger

logger = get_logger("main")

app = FastAPI()

sdk = CopilotKitSDK(
    agents=[
        # LangGraphAgent(
        #     name="chat_agent",
        #     description="An example for showcasing the  AG-UI protocol using LangGraph.",
        #     graph=router_graph
        # ),
        LangGraphAgent(
            name="chat_agent",
            description="An example for showcasing the  AG-UI protocol using LangGraph.",
            graph=federated_monitoring_graph
        )
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
        "agent.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )

if __name__ == "__main__":
    main()

