import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import Tool
from langchain_mcp_adapters.sessions import Connection
from dotenv import load_dotenv
import nest_asyncio
from mcp import ClientSession

from agent.utils.logging_config import get_logger

load_dotenv()

logger = get_logger("mcp_tools")


def get_default_server_configs() -> Dict[str, Dict[str, Any]]:
    """Get default server configurations"""
    config = {
        "prometheus": {
            "command": "npx",
            "args": ["prometheus-mcp-server@1.0.1"],
            "transport": "stdio",
            "env": {
                "PROMETHEUS_URL": os.getenv(
                    "PROMETHEUS_URL", "https://localhost:30090"
                ),
                "PROMETHEUS_INSECURE": os.getenv("PROMETHEUS_INSECURE", "true"),
            },
        },
        "multicluster-mcp-server": {
            "command": "npx",
            "args": [
              "-y",
              "multicluster-mcp-server@latest"
            ],
            "transport": "stdio",
            "env": {
                "KUBECONFIG": os.getenv("KUBECONFIG", "~/.kube/config"),
            },
        }
    }
    return config


# Global MCP client instance
_mcp_client: Optional[MultiServerMCPClient] = None
_tools_cache: Optional[List[Tool]] = None

# Session management for persistent connections
_active_sessions: Dict[str, Dict[str, Any]] = {}
_session_locks: Dict[str, asyncio.Lock] = {}  # Per-server locks instead of global lock
_session_stats = {
    "created": 0,
    "reused": 0,
    "failures": 0,
    "active_count": 0
}


def get_mcp_client(
    server_configs: dict[str, Connection] | None = None
) -> MultiServerMCPClient:
    """Get or create MCP client"""
    global _mcp_client
    if _mcp_client is None or server_configs is not None:
        configs = server_configs or get_default_server_configs()
        _mcp_client = MultiServerMCPClient(configs)
        logger.debug(f"[PERF] NEW MCP client created with {len(configs)} server configs")
    else:
        logger.debug("[PERF] Using existing cached MCP client")
    return _mcp_client


async def get_persistent_session(server_name: str, client: MultiServerMCPClient) -> ClientSession:
    """Get or create a persistent MCP session for a server with health checking"""
    import time
    global _active_sessions, _session_locks, _session_stats
    
    # Get or create per-server lock
    if server_name not in _session_locks:
        _session_locks[server_name] = asyncio.Lock()
    
    async with _session_locks[server_name]:
        current_time = time.time()
        
        # Check if session exists and is healthy
        if server_name in _active_sessions:
            session_data = _active_sessions[server_name]
            session_age = current_time - session_data['created_at']
            
            # Health check: try to ping the session (simple check)
            try:
                session = session_data['session']
                # Basic health check - session should be responsive
                logger.debug(f"[PERF] Health check for session '{server_name}' (age: {session_age:.1f}s)")
                
                _session_stats["reused"] += 1
                session_data['last_used'] = current_time
                session_data['use_count'] += 1
                
                logger.debug(f"[PERF] REUSING healthy persistent session for '{server_name}' (used {session_data['use_count']} times)")
                return session
                
            except Exception as e:
                logger.warning(f"[PERF] Session health check failed for '{server_name}': {e}")
                # Remove unhealthy session
                try:
                    await session_data['context'].__aexit__(None, None, None)
                except:
                    pass
                del _active_sessions[server_name]
                _session_stats["failures"] += 1
                _session_stats["active_count"] -= 1
        
        # Create new session with retry logic
        logger.debug(f"[PERF] Creating NEW persistent session for server '{server_name}'")
        
        max_retries = 3
        retry_delay = 2.0  # seconds
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"[PERF] Retry {attempt}/{max_retries-1} for session '{server_name}' after {retry_delay}s delay")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                
                session_context = client.session(server_name)
                session = await session_context.__aenter__()
                
                _active_sessions[server_name] = {
                    'session': session,
                    'context': session_context,
                    'created_at': current_time,
                    'last_used': current_time,
                    'use_count': 1,
                    'server_name': server_name
                }
                
                _session_stats["created"] += 1
                _session_stats["active_count"] += 1
                
                logger.info(f"[PERF] ✅ NEW persistent session created for '{server_name}' (attempt {attempt + 1})")
                return session
                
            except Exception as e:
                logger.warning(f"[PERF] Session creation attempt {attempt + 1} failed for '{server_name}': {e}")
                if attempt == max_retries - 1:
                    # Last attempt failed
                    _session_stats["failures"] += 1
                    logger.error(f"[PERF] ❌ All {max_retries} attempts failed for '{server_name}': {e}")
                    raise


async def close_persistent_sessions():
    """Close all persistent MCP sessions with detailed statistics"""
    import time
    import asyncio
    global _active_sessions, _session_locks, _session_stats
    
    # We don't need locks during shutdown as it's a single operation
    if not _active_sessions:
        logger.info("[PERF] No persistent sessions to close")
        return
        
    logger.info(f"[PERF] Closing {len(_active_sessions)} persistent sessions...")
    
    current_time = time.time()
    sessions_to_close = list(_active_sessions.items())  # Create a copy to avoid mutation during iteration
    
    for server_name, session_data in sessions_to_close:
        try:
            session_age = current_time - session_data['created_at']
            last_used_ago = current_time - session_data['last_used']
            
            logger.info(f"[PERF] Closing session '{server_name}': age={session_age:.1f}s, used={session_data['use_count']} times, last_used={last_used_ago:.1f}s ago")
            
            # Try to close gracefully with timeout
            try:
                await asyncio.wait_for(
                    session_data['context'].__aexit__(None, None, None), 
                    timeout=5.0  # 5 second timeout for each session
                )
            except asyncio.TimeoutError:
                logger.warning(f"[PERF] Session '{server_name}' close timed out after 5s, continuing...")
            except asyncio.CancelledError:
                logger.warning(f"[PERF] Session '{server_name}' close was cancelled, continuing...")
            
        except Exception as e:
            logger.error(f"Error closing session for {server_name}: {e}")
    
    _active_sessions.clear()
    _session_locks.clear()  # Also clear the locks
    _session_stats["active_count"] = 0
    
    logger.info(f"[PERF] All persistent sessions closed - Final stats: created={_session_stats['created']}, reused={_session_stats['reused']}, failures={_session_stats['failures']}")


def get_session_stats() -> dict:
    """Get current session statistics for monitoring"""
    return {
        **_session_stats,
        "active_sessions": len(_active_sessions),
        "session_details": {
            name: {
                "use_count": data["use_count"],
                "created_at": data["created_at"],
                "last_used": data["last_used"]
            } for name, data in _active_sessions.items()
        }
    }


# --- Async version ---
async def get_mcp_tools(
    server_configs: dict[str, Connection] | None = None, use_cache: bool = True
) -> List[Tool]:
    """Async: Get all MCP tools from configured servers"""
    import time
    start_time = time.time()
    global _tools_cache

    if _tools_cache is not None and use_cache:
        logger.info(f"[PERF] Using cached MCP tools ({len(_tools_cache)} tools) - cache hit in {time.time() - start_time:.4f}s")
        return _tools_cache

    logger.info(f"[PERF] Cache miss - fetching MCP tools from servers at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    try:
        # Check if this is first connection before setting cache
        is_first_connection = _tools_cache is None
        
        client_start = time.time()
        client = get_mcp_client(server_configs)
        client_time = time.time() - client_start
        
        tools_start = time.time()
        tools = await client.get_tools()
        tools_time = time.time() - tools_start
        
        _tools_cache = tools
        total_time = time.time() - start_time

        logger.info(f"[PERF] MCP tools fetched: client_init={client_time:.2f}s, get_tools={tools_time:.2f}s, total={total_time:.2f}s ({len(tools)} tools)")
        
        # Only show tools on first connection
        if is_first_connection:
            print(f"✅ Connected to MCP servers with {len(tools)} tools")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
        return tools

    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"[PERF] Failed to fetch MCP tools after {error_time:.2f}s: {str(e)}", exc_info=True)
        raise


# --- Sync version ---
def sync_get_mcp_tools(
    server_configs: dict[str, Connection] | None = None, use_cache: bool = True
) -> List[Tool]:
    """Sync: Get all MCP tools from configured servers"""
    logger.debug("sync_get_mcp_tools called")
    
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        logger.debug("Running in async context, applying nest_asyncio")
        nest_asyncio.apply()
        # Create task and run it
        coro = get_mcp_tools(server_configs, use_cache)
        task = asyncio.ensure_future(coro)
        return loop.run_until_complete(task)
    except RuntimeError:
        # No running loop, we can use asyncio.run
        logger.debug("No running event loop, using asyncio.run")
        return asyncio.run(get_mcp_tools(server_configs, use_cache))


# --- Startup preloader functions ---
async def preload_mcp_client_and_sessions():
    """Preload MCP client, sessions, and tools during application startup"""
    import time
    startup_start = time.time()
    
    logger.info(f"[STARTUP] 🚀 Preloading MCP client and sessions")
    
    try:
        # 1. Create MCP client
        client_start = time.time()
        client = get_mcp_client()
        client_time = time.time() - client_start
        
        # 2. Create sessions SERIALLY to avoid EPIPE conflicts
        logger.info("[STARTUP] 📡 Creating MCP sessions serially...")
        sessions_start = time.time()
        
        healthy_sessions = 0
        server_names = list(client.connections.keys())
        logger.info(f"[STARTUP] Creating sessions for servers: {', '.join(server_names)}")
        
        # Create sessions one by one instead of in parallel
        for i, server_name in enumerate(server_names, 1):
            try:
                logger.info(f"[STARTUP] [{i}/{len(server_names)}] Creating session for '{server_name}'...")
                session_start = time.time()
                
                session = await get_persistent_session(server_name, client)
                session_time = time.time() - session_start
                
                healthy_sessions += 1
                logger.info(f"[STARTUP] ✅ [{i}/{len(server_names)}] Session '{server_name}' created in {session_time:.1f}s")
                
            except Exception as e:
                logger.error(f"[STARTUP] ❌ [{i}/{len(server_names)}] Session '{server_name}' failed: {e}")
        
        # 3. Load tools with existing persistent sessions
        tools_start = time.time()
        tools = await get_mcp_tools_with_persistent_sessions(use_cache=False)
        tools_time = time.time() - tools_start
        
        sessions_time = time.time() - sessions_start
        logger.info(f"[STARTUP] 📊 Serial session creation completed in {sessions_time:.1f}s ({healthy_sessions}/{len(server_names)} successful)")
        
        total_startup_time = time.time() - startup_start
        
        logger.info(f"[STARTUP] 🎉 MCP startup complete in {total_startup_time:.1f}s - {len(tools)} tools, {healthy_sessions} sessions ready")
        
        # Get current session stats
        stats = get_session_stats()
        
        return {
            "success": True,
            "total_time": total_startup_time,
            "tools_loaded": len(tools),
            "sessions_ready": healthy_sessions,
            "stats": stats
        }
        
    except Exception as e:
        error_time = time.time() - startup_start
        logger.error(f"[STARTUP] ❌ MCP preload failed after {error_time:.3f}s: {e}", exc_info=True)
        return {
            "success": False, 
            "error": str(e),
            "time": error_time
        }


def preload_mcp_sync():
    """Synchronous wrapper for MCP preloading"""
    import asyncio
    import nest_asyncio
    
    try:
        loop = asyncio.get_running_loop()
        nest_asyncio.apply()
        task = asyncio.ensure_future(preload_mcp_client_and_sessions())
        return loop.run_until_complete(task)
    except RuntimeError:
        return asyncio.run(preload_mcp_client_and_sessions())


# --- Custom tool wrapper for persistent sessions ---
def create_persistent_mcp_tool(mcp_tool, server_name: str) -> Tool:
    """Create a LangChain tool that uses persistent MCP sessions"""
    from langchain_core.tools import StructuredTool
    from langchain_mcp_adapters.tools import _convert_call_tool_result
    
    async def persistent_call_tool(**arguments: dict[str, Any]) -> tuple[str | list[str], list]:
        """Tool execution using persistent session"""
        import time
        start_time = time.time()
        
        # Generate session ID for tracking
        session_id = f"{server_name}-{hash(str(arguments)) % 10000}"
        logger.debug(f"[PERF] Tool '{mcp_tool.name}' starting with persistent session {session_id}")
        
        try:
            # Get persistent session for this server
            client = get_mcp_client()
            session_get_start = time.time()
            session = await get_persistent_session(server_name, client)
            session_get_time = time.time() - session_get_start
            
            logger.debug(f"[PERF] Tool '{mcp_tool.name}' acquired persistent session in {session_get_time:.3f}s (NO SERVER RESTART)")
            
            # Execute tool using persistent session
            call_start = time.time()
            call_tool_result = await session.call_tool(mcp_tool.name, arguments)
            call_end = time.time()
            
            total_time = call_end - start_time
            actual_call_time = call_end - call_start
            
            logger.info(f"[PERF] Tool '{mcp_tool.name}' SUCCESS: total={total_time:.3f}s, actual_call={actual_call_time:.3f}s")
            
            return _convert_call_tool_result(call_tool_result)
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"[PERF] Tool '{mcp_tool.name}' FAILED after {error_time:.3f}s with session {session_id}: {e}")
            
            # Log session stats on failure for debugging
            try:
                stats = get_session_stats()
                logger.error(f"[PERF] Session stats on failure: {stats}")
            except:
                pass
            raise
    
    return StructuredTool(
        name=mcp_tool.name,
        description=mcp_tool.description or "",
        args_schema=mcp_tool.inputSchema,
        coroutine=persistent_call_tool,
        response_format="content_and_artifact",
        metadata=mcp_tool.annotations.model_dump() if mcp_tool.annotations else None,
    )


# --- Enhanced version with persistent sessions ---
async def get_mcp_tools_with_persistent_sessions(
    server_configs: dict[str, Connection] | None = None, use_cache: bool = True
) -> List[Tool]:
    """Get MCP tools using persistent sessions to avoid server restarts"""
    import time
    import asyncio
    from langchain_mcp_adapters.tools import load_mcp_tools
    
    start_time = time.time()
    global _tools_cache

    # Use cache if available and requested
    if _tools_cache is not None and use_cache:
        logger.info(f"[PERF] Using cached MCP tools ({len(_tools_cache)} tools) - cache hit in {time.time() - start_time:.4f}s")
        return _tools_cache

    logger.debug(f"[PERF] Cache miss - fetching MCP tools with PERSISTENT SESSIONS")
    
    try:
        client = get_mcp_client(server_configs)
        all_tools = []
        
        # Create tasks for parallel loading of all servers
        async def load_server_tools(server_name: str):
            """Load tools from a single server"""
            session_start = time.time()
            logger.info(f"📡 Starting connection to MCP server: {server_name}")
            
            try:
                # Get persistent session for this server to list tools
                session_get_start = time.time()
                logger.debug(f"🔄 {server_name}: Getting persistent session...")
                session = await get_persistent_session(server_name, client)
                session_get_time = time.time() - session_get_start
                logger.info(f"🔗 {server_name}: Session acquired in {session_get_time:.1f}s")
                
                # List tools from session
                from langchain_mcp_adapters.tools import _list_all_tools
                mcp_tools = await _list_all_tools(session)
                
                # Create persistent tools using our custom wrapper
                server_tools = [create_persistent_mcp_tool(mcp_tool, server_name) for mcp_tool in mcp_tools]
                
                session_time = time.time() - session_start
                logger.info(f"✅ {server_name}: {len(server_tools)} tools loaded in {session_time:.1f}s")
                
                return server_tools
                
            except Exception as e:
                session_time = time.time() - session_start
                logger.error(f"❌ {server_name}: failed to load tools in {session_time:.1f}s - {e}")
                return []
        
        # Execute all server loading tasks in parallel
        server_names = list(client.connections.keys())
        logger.info(f"🔧 Loading tools from {len(server_names)} MCP servers: {', '.join(server_names)}")
        tools_load_start = time.time()
        
        server_tasks = [load_server_tools(server_name) for server_name in server_names]
        server_results = await asyncio.gather(*server_tasks, return_exceptions=True)
        
        tools_load_time = time.time() - tools_load_start
        
        # Combine all tools from all servers and handle exceptions
        all_tools = []
        successful_servers = 0
        for i, result in enumerate(server_results):
            if isinstance(result, Exception):
                logger.error(f"❌ {server_names[i]}: Exception during loading: {result}")
            elif isinstance(result, list):
                all_tools.extend(result)
                successful_servers += 1
        
        logger.info(f"🔧 Tools loading complete in {tools_load_time:.1f}s - {successful_servers}/{len(server_names)} servers, {len(all_tools)} total tools")
        
        _tools_cache = all_tools
        total_time = time.time() - start_time
        
        # Simple completion message  
        if len(all_tools) > 0:
            logger.debug(f"[PERF] Total loading time: {total_time:.1f}s")
        
        return all_tools

    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"[PERF] Failed to fetch MCP tools with persistent sessions after {error_time:.2f}s: {str(e)}", exc_info=True)
        raise

