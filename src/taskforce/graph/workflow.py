from langgraph.graph import StateGraph, START, END

from taskforce.graph.state import GraphState
from taskforce.graph.nodes import (
    approval_node,
    brain_node,
    response_node,
    route_after_approval,
    route_after_router,
    router_node,
)


def build_graph() -> StateGraph:
    """Build the TaskForce AI workflow graph."""
    builder = StateGraph(GraphState)

    # Add nodes
    builder.add_node("router", router_node)
    builder.add_node("brain", brain_node)
    builder.add_node("approval", approval_node)
    builder.add_node("response", response_node)

    # Edges
    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", route_after_router, {"brain": "brain", "approval": "approval"})
    builder.add_edge("brain", "response")
    builder.add_conditional_edges("approval", route_after_approval, {"brain": "brain", "response": "response"})
    builder.add_edge("response", END)

    return builder


def compile_graph(checkpointer=None):
    """Compile the graph, optionally with a checkpointer."""
    return build_graph().compile(checkpointer=checkpointer)


# Graph without checkpointer for LangGraph Studio and simple testing
graph = compile_graph()
