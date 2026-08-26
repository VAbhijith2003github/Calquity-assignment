"""
graph.py
--------
Compiles the full LangGraph StateGraph pipeline for the ParcelPilot agent.

Graph structure:
    START
      │
    understand
      │
    plan
      │
    gather_evidence
      │
    resolve_sources
      │
    make_decision
      │
    ┌──┴──────────────┐
    │                 │
  generate_response  request_approval
                       │
                 ┌─────┴─────┐
                 │           │
            generate_response  execute_action
                                   │
                              generate_response
                                   │
                                  END
"""

from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    understand_request,
    plan,
    gather_evidence,
    resolve_sources,
    make_decision,
    request_approval,
    execute_action,
    generate_response,
)
from .router import route_after_decision, route_after_approval

# ── Build the State Graph ────────────────────────────────────────────────────

workflow = StateGraph(AgentState)

# Register all 8 nodes
workflow.add_node("understand", understand_request)
workflow.add_node("plan", plan)
workflow.add_node("gather_evidence", gather_evidence)
workflow.add_node("resolve_sources", resolve_sources)
workflow.add_node("make_decision", make_decision)
workflow.add_node("request_approval", request_approval)
workflow.add_node("execute_action", execute_action)
workflow.add_node("generate_response", generate_response)

# Set graph entry point
workflow.set_entry_point("understand")

# ── Define Edges ─────────────────────────────────────────────────────────────

# Linear flow: understand → plan → gather → resolve → decide
workflow.add_edge("understand", "plan")
workflow.add_edge("plan", "gather_evidence")
workflow.add_edge("gather_evidence", "resolve_sources")
workflow.add_edge("resolve_sources", "make_decision")

# Conditional branch after decision: action needed vs direct answer
workflow.add_conditional_edges(
    "make_decision",
    route_after_decision,
    {
        "request_approval": "request_approval",
        "generate_response": "generate_response"
    }
)

# Conditional branch after approval: confirmed vs cancelled
workflow.add_conditional_edges(
    "request_approval",
    route_after_approval,
    {
        "execute_action": "execute_action",
        "generate_response": "generate_response"
    }
)

# Execute → respond, then end
workflow.add_edge("execute_action", "generate_response")
workflow.add_edge("generate_response", END)

# ── Compile ──────────────────────────────────────────────────────────────────

compiled_app = workflow.compile()
