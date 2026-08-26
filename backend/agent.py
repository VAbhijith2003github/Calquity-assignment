"""
agent.py
--------
Thin compatibility shim. Delegates all processing to the
full LangGraph pipeline in app/agent/graph.py.
"""

import logging
from typing import Dict, Any, Optional

from app.agent.graph import compiled_app

logger = logging.getLogger("backend.agent")


class ParcelPilotAgent:
    """
    Entry point for the ParcelPilot conversational agent.
    Wraps the compiled LangGraph pipeline.
    """

    def process_message(
        self,
        message: str,
        account_id: Optional[str] = None,
        conversation_history: list = None,
        approved: Optional[bool] = None,
        pending_action: Optional[Dict] = None,
        stream_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Runs the compiled LangGraph state machine for the given message.

        Args:
            message: The user's natural language input.
            account_id: Active session account boundary (None = full access).
            conversation_history: Prior messages for multi-turn context.
            approved: True/False if this is a confirmation response.
            pending_action: Previously proposed action to re-inject on confirmation.
            stream_callback: Callback invoked during token streaming.

        Returns:
            dict with keys: text, pending_action, tool_used, execution_trace
        """
        messages = list(conversation_history or [])
        messages.append({"role": "user", "content": message})

        initial_state = {
            "messages": messages,
            "intent": None,
            "entities": {"account_id": account_id} if account_id else {},
            "session_account_id": account_id,
            "retrieved_documents": [],
            "operational_data": {},
            "resolved_sources": [],
            "conflicts": [],
            "decision": None,
            "pending_action": pending_action,
            "approval_required": False,
            "approved": approved,
            "action_result": None,
            "execution_trace": [],
            "final_response": None,
        }

        logger.info(f"[ParcelPilotAgent] Invoking LangGraph — account_id={account_id}")
        config = {}
        if stream_callback:
            config = {"configurable": {"stream_callback": stream_callback}}
        
        try:
            final_state = compiled_app.invoke(initial_state, config=config)
        except Exception as e:
            logger.error(f"[ParcelPilotAgent] Invocation failed: {e}")
            err_msg = str(e).lower()
            if "quota" in err_msg or "exhausted" in err_msg or "429" in err_msg or "503" in err_msg or "unavailable" in err_msg:
                fallback_msg = "⚠️ **API token limit reached.** Please wait a few seconds and try again."
            else:
                fallback_msg = "I was unable to process your request. Please contact ParcelPilot support."
            if stream_callback:
                stream_callback(fallback_msg)
            return {
                "text": fallback_msg,
                "pending_action": None,
                "tool_used": "error",
                "execution_trace": ["⚠️ Pipeline execution crashed due to external API limit/error."]
            }

        return {
            "text": final_state.get("final_response", "I was unable to process your request."),
            "pending_action": final_state.get("pending_action"),
            "tool_used": final_state.get("tool_used"),
            "execution_trace": final_state.get("execution_trace", []),
        }
