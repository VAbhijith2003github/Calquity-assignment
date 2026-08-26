"""
state.py
--------
Defines the shared AgentState TypedDict that flows through
every node of the LangGraph pipeline.
"""

from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict):
    # Conversation history (list of {"role": "user"|"assistant", "content": str})
    messages: List[Any]

    # Request understanding (Phase 3)
    intent: Optional[str]
    entities: Dict[str, Any]
    # Trusted server-side session scope. Never derive this from LLM entities.
    session_account_id: Optional[str]

    # Evidence collected (Phase 5)
    retrieved_documents: List[Dict]
    operational_data: Dict[str, Any]

    # Policy processing (Phase 6)
    resolved_sources: List[Dict]
    conflicts: List[Dict]

    # Decision (Phase 7)
    decision: Optional[Dict[str, Any]]

    # Action (Phase 8-10)
    pending_action: Optional[Dict[str, Any]]
    approval_required: bool
    approved: Optional[bool]
    action_result: Optional[Dict[str, Any]]

    # Output (Phase 11)
    execution_trace: List[str]
    final_response: Optional[str]
