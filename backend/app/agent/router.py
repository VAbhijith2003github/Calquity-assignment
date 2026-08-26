"""
router.py
---------
Conditional edge functions that control flow between nodes
in the LangGraph state machine.
"""

from .state import AgentState


def route_after_plan(state: AgentState) -> str:
    """Always gathers evidence after planning. Simple passthrough."""
    return "gather_evidence"


def route_after_decision(state: AgentState) -> str:
    """
    After making a decision, determine next step:
    - If action is needed → request_approval
    - Otherwise → generate_response
    """
    decision = state.get("decision", {})
    recommended_action = decision.get("recommended_action")

    if recommended_action and recommended_action != "null":
        return "request_approval"
    return "generate_response"


def route_after_approval(state: AgentState) -> str:
    """
    After the user is asked to approve:
    - If approved == True → execute_action
    - If approved == False or None → generate_response (rejection/cancel)
    """
    approved = state.get("approved")

    if approved is True:
        return "execute_action"
    return "generate_response"
