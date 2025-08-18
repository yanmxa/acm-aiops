"""
Session configuration management for thread_id and run_id
"""

import uuid
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from agent.utils.logging_config import get_logger

logger = get_logger("session_config")

def create_session_config(thread_id: str = None, run_id: str = None) -> RunnableConfig:
    """
    Create a RunnableConfig with thread_id and run_id for session management
    
    Args:
        thread_id: Optional thread ID. If None, generates a new UUID
        run_id: Optional run ID. If None, generates a new UUID
        
    Returns:
        RunnableConfig with configurable thread_id and run_id
    """
    if thread_id is None:
        thread_id = f"thread-{uuid.uuid4().hex[:8]}"
    
    if run_id is None:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
    
    config = RunnableConfig(
        configurable={
            "thread_id": thread_id,
            "run_id": run_id
        }
    )
    
    logger.info(f"Created session config - thread_id: {thread_id}, run_id: {run_id}")
    return config

def get_session_info(config: RunnableConfig) -> Dict[str, str]:
    """
    Extract session information from RunnableConfig
    
    Args:
        config: RunnableConfig containing session information
        
    Returns:
        Dictionary with thread_id and run_id
    """
    if not config or not config.get("configurable"):
        return {"thread_id": "unknown", "run_id": "unknown"}
    
    configurable = config["configurable"]
    return {
        "thread_id": configurable.get("thread_id", "unknown"),
        "run_id": configurable.get("run_id", "unknown")
    }

def create_new_run_config(thread_id: str) -> RunnableConfig:
    """
    Create a new run config for an existing thread
    
    Args:
        thread_id: Existing thread ID
        
    Returns:
        RunnableConfig with same thread_id but new run_id
    """
    return create_session_config(thread_id=thread_id, run_id=None)

def log_session_activity(config: RunnableConfig, activity: str, node: str = None):
    """
    Log session activity with session context
    
    Args:
        config: RunnableConfig containing session information
        activity: Description of the activity
        node: Optional node name
    """
    session_info = get_session_info(config)
    node_info = f"[{node}] " if node else ""
    logger.info(f"{node_info}Session {session_info['thread_id']}/{session_info['run_id']}: {activity}")