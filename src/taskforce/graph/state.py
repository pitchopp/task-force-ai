from typing import Annotated, TypedDict

from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class GraphState(TypedDict):
    """State flowing through the LangGraph workflow."""

    messages: Annotated[list[BaseMessage], add_messages]
    chat_id: int
    user_id: int
    thread_id: str
    response: str
    needs_approval: bool
    approval_id: str
    approval_action: str
    approval_decision: str
