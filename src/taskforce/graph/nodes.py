import logging

from langchain_core.messages import AIMessage, HumanMessage

from taskforce.graph.state import GraphState
from taskforce.orchestrator.brain import think
from taskforce.orchestrator.approval import (
    create_approval_request,
    wait_for_decision,
)

logger = logging.getLogger(__name__)


async def router_node(state: GraphState) -> GraphState:
    """Analyze user intent and route to appropriate next step."""
    # For now, all messages go to the brain.
    # Future: could classify intent, check for pending approvals, etc.
    return state


async def brain_node(state: GraphState) -> GraphState:
    """Core agent processing via Claude Agent SDK."""
    last_message = state["messages"][-1]
    user_text = last_message.content if isinstance(last_message, HumanMessage) else str(last_message.content)

    logger.info("Brain processing message from user %d", state["user_id"])

    response = await think(user_text, messages=state["messages"])

    return {
        **state,
        "response": response,
        "messages": [AIMessage(content=response)],
    }


async def approval_node(state: GraphState) -> GraphState:
    """Handle human-in-the-loop approval."""
    approval_id = await create_approval_request(
        task_id=state["thread_id"],
        chat_id=state["chat_id"],
        action_description=state.get("approval_action", "Action requiring approval"),
        risk_level="high",
    )

    decision = await wait_for_decision(approval_id)

    return {
        **state,
        "approval_id": approval_id,
        "approval_decision": decision,
    }


async def response_node(state: GraphState) -> GraphState:
    """Final node — the response is already in state, ready to be sent."""
    return state


def route_after_router(state: GraphState) -> str:
    """Decide where to go after routing."""
    if state.get("needs_approval"):
        return "approval"
    return "brain"


def route_after_approval(state: GraphState) -> str:
    """Decide where to go after approval."""
    if state.get("approval_decision") == "approved":
        return "brain"
    return "response"
