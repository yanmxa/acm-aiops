from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
import os

class NodeInfo(TypedDict):
    node_name: str
    node_status: str  # "active", "completed", "pending"
    node_message: str

class WorkflowProgress(TypedDict):
    nodes_info: List[NodeInfo]

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_query: str
    workflow_progress: WorkflowProgress
