from fastapi import FastAPI
import os
import time
import uvicorn
import signal
import asyncio
from contextlib import asynccontextmanager

# CopilotKit imports
from copilotkit import  CopilotKitSDK, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint

# from agent.graphs.router_graph import router_graph
from agent.federated_learning.monitoring.workflow import federated_monitoring_graph
from agent.utils.session_config import create_session_config
from agent.utils.logging_config import get_logger
from agent.tools.mcp_tool import close_persistent_sessions, preload_mcp_client_and_sessions, get_session_stats

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown with MCP preloading"""
    import time
    app_start = time.time()
    
    logger.info("🚀 Starting FastAPI application with MCP preloading...")
    
    # Startup: Preload MCP client and sessions
    try:
        preload_result = await preload_mcp_client_and_sessions()
        
        if preload_result["success"]:
            logger.info(f"✅ MCP preloading complete in {preload_result['total_time']:.1f}s - {preload_result['tools_loaded']} tools, {preload_result['sessions_ready']} sessions")
        else:
            logger.error(f"❌ MCP preloading failed: {preload_result['error']}")
            logger.warning("⚠️  Application will start but MCP performance may be degraded")
    
    except Exception as e:
        logger.error(f"❌ Critical error during MCP preloading: {e}", exc_info=True)
        logger.warning("⚠️  Application will start but MCP may not work properly")
    
    total_startup = time.time() - app_start
    logger.info(f"🎉 FastAPI application ready in {total_startup:.1f}s")
    
    yield
    
    # Shutdown: Clean up MCP sessions
    logger.info("🛑 Shutting down - cleaning up MCP persistent sessions")
    
    try:
        # Log final session stats
        final_stats = get_session_stats()
        logger.info(f"📊 Final session stats: {final_stats}")
        
        await close_persistent_sessions()
        logger.info("✅ FastAPI application shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}", exc_info=True)

app = FastAPI(lifespan=lifespan)

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
    return {"message": "Hello World!!", "status": "ready"}


@app.get("/health/mcp")
async def mcp_health():
    """Check MCP client and session health status"""
    try:
        stats = get_session_stats()
        
        return {
            "status": "healthy" if stats["active_sessions"] > 0 else "no_sessions",
            "mcp_client_loaded": True,
            "session_stats": stats,
            "timestamp": time.strftime('%H:%M:%S')
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "mcp_client_loaded": False,
            "timestamp": time.strftime('%H:%M:%S')
        }


@app.get("/health")
async def health():
    """General application health check"""
    import time
    mcp_status = await mcp_health()
    
    return {
        "application": "healthy",
        "mcp": mcp_status,
        "timestamp": time.strftime('%H:%M:%S'),
        "uptime_info": "Check /health/mcp for detailed MCP session information"
    }


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

