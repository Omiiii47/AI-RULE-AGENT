from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import extraction_node, validation_node, update_node, response_node


def route_after_validation(state: AgentState) -> str:
    return "update" if state.get("is_valid") else "response"


def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("extract", extraction_node)
    graph.add_node("validate", validation_node)
    graph.add_node("update", update_node)
    graph.add_node("response", response_node)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "validate")
    graph.add_conditional_edges(
        "validate",
        route_after_validation,
        {"update": "update", "response": "response"},
    )
    graph.add_edge("update", "response")
    graph.add_edge("response", END)

    return graph.compile()


agent_app = build_agent()
