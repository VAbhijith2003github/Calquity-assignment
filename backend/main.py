import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure workspace root is in sys.path
workspace_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(workspace_dir))

from backend.agent import ParcelPilotAgent
from backend.tools import DatabaseTools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")

app = FastAPI(title="ParcelPilot Support & Operations Copilot")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-Memory Session Storage ───────────────────────────────────────────────
# Default: Priya Mehta (Internal Support Agent)
session_state = {
    "account_id": None,           # None means full internal support access
    "role": "support_agent",      # "support_agent" or "customer"
    "user_name": "Priya Mehta (CSM)",
    "pending_action": None,       # Holds proposed action waiting for confirmation
    "conversation_history": [],   # Multi-turn conversation context
}

agent = ParcelPilotAgent()
db = DatabaseTools()

# ── API Models ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

class SessionUpdateRequest(BaseModel):
    account_id: Optional[str]
    role: str
    user_name: str

class ConfirmRequest(BaseModel):
    confirm: bool

# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/session")
def get_session():
    """Gets the active session details."""
    return {
        "account_id": session_state["account_id"],
        "role": session_state["role"],
        "user_name": session_state["user_name"],
    }

@app.post("/api/session")
def update_session(req: SessionUpdateRequest):
    """Updates the active session details and clears pending actions and history."""
    global session_state
    session_state["account_id"] = req.account_id
    session_state["role"] = req.role
    session_state["user_name"] = req.user_name
    session_state["pending_action"] = None
    session_state["conversation_history"] = []
    logger.info(f"Session changed to: {req.user_name} (Role: {req.role}, Account: {req.account_id})")
    return {"message": f"Session changed to {req.user_name}", "session": get_session()}

@app.get("/api/db-view")
def get_db_view():
    """Returns database tables scoped to the active session account."""
    account_id = session_state["account_id"]
    return {
        "accounts": db.get_accounts(account_id),
        "orders": db.get_orders(account_id),
        "tickets": db.get_tickets(account_id)
    }

import json
import queue
import threading
from fastapi.responses import StreamingResponse

@app.post("/api/chat")
def chat(req: ChatRequest):
    """
    Processes user messages through the full LangGraph pipeline.
    Passes conversation history for multi-turn context.
    Streams back text chunks and metadata via SSE.
    """
    account_id = session_state["account_id"]
    history = session_state.get("conversation_history", [])

    q = queue.Queue()

    def stream_callback(token: str):
        q.put(("chunk", token))

    def run_agent():
        try:
            response = agent.process_message(
                message=req.message,
                account_id=account_id,
                conversation_history=history,
                stream_callback=stream_callback,
            )
            q.put(("metadata", response))
        except Exception as e:
            logger.error(f"Error running agent thread: {e}")
            q.put(("error", str(e)))

    t = threading.Thread(target=run_agent)
    t.start()

    def event_generator():
        # Yield initial status trace log
        yield f"event: trace\ndata: {json.dumps({'message': 'Initializing agent...'})}\n\n"

        while True:
            try:
                item = q.get(timeout=60)
            except queue.Empty:
                yield f"event: error\ndata: {json.dumps({'error': 'Timeout waiting for response'})}\n\n"
                break

            event_type, val = item
            if event_type == "chunk":
                yield f"event: chunk\ndata: {json.dumps({'text': val})}\n\n"
            elif event_type == "metadata":
                # Persist pending action to session for the /api/confirm endpoint
                if val.get("pending_action"):
                    session_state["pending_action"] = val["pending_action"]
                else:
                    session_state["pending_action"] = None

                # Append this exchange to conversation history (multi-turn support)
                session_state["conversation_history"].append({"role": "user", "content": req.message})
                if val.get("text"):
                    session_state["conversation_history"].append({"role": "assistant", "content": val["text"]})

                # Trim history to last 10 messages to avoid context bloat
                session_state["conversation_history"] = session_state["conversation_history"][-10:]

                # Yield metadata event to client
                metadata = {
                    "text": val.get("text", ""),
                    "has_pending": val.get("pending_action") is not None,
                    "pending_action": val.get("pending_action"),
                    "tool_used": val.get("tool_used"),
                    "execution_trace": val.get("execution_trace", []),
                }
                yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"
                break
            elif event_type == "error":
                yield f"event: error\ndata: {json.dumps({'error': val})}\n\n"
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/confirm")
def confirm_action(req: ConfirmRequest):
    """
    Resumes the LangGraph pipeline with the user's approval decision.
    Re-invokes the agent with approved=True/False and the stored pending_action.
    """
    global session_state
    pending = session_state.get("pending_action")

    if not pending:
        raise HTTPException(status_code=400, detail="No pending action to confirm.")

    if not req.confirm:
        session_state["pending_action"] = None
        return {"message": "Action cancelled. No changes were made."}

    # Re-invoke the agent with approved=True and the pending action
    account_id = session_state["account_id"]
    history = session_state.get("conversation_history", [])
    user_message = "Confirmed, please proceed."

    response = agent.process_message(
        message=user_message,
        account_id=account_id,
        conversation_history=history,
        approved=True,
        pending_action=pending,
    )

    session_state["pending_action"] = None

    return {
        "message": response.get("text", "Action completed."),
        "tool_used": response.get("tool_used"),
        "execution_trace": response.get("execution_trace", []),
    }
