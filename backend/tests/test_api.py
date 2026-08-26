import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure workspace root and backend dir are in sys.path
backend_dir = Path(__file__).resolve().parent.parent
workspace_dir = backend_dir.parent
import sys
if str(workspace_dir) not in sys.path:
    sys.path.insert(0, str(workspace_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Mock the database/agent modules to avoid starting real agents/DB connections during import/test setup
with patch("backend.main.ParcelPilotAgent") as mock_agent_class, patch("backend.main.DatabaseTools") as mock_db_class:
    from backend.main import app, session_state

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_session_state():
    """Reset session state before each test."""
    session_state["account_id"] = None
    session_state["role"] = "support_agent"
    session_state["user_name"] = "Priya Mehta (CSM)"
    session_state["pending_action"] = None
    session_state["conversation_history"] = []


def test_get_session():
    """Test GET /api/session returns the active session state."""
    response = client.get("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] is None
    assert data["role"] == "support_agent"
    assert data["user_name"] == "Priya Mehta (CSM)"


def test_update_session():
    """Test POST /api/session updates the session state and resets history."""
    session_state["conversation_history"] = [{"role": "user", "content": "hello"}]
    session_state["pending_action"] = {"action": "some_action"}

    payload = {
        "account_id": "ACC123",
        "role": "customer",
        "user_name": "Test User"
    }
    response = client.post("/api/session", json=payload)
    assert response.status_code == 200
    
    # Assert return value
    data = response.json()
    assert data["message"] == "Session changed to Test User"
    assert data["session"]["account_id"] == "ACC123"
    assert data["session"]["role"] == "customer"
    assert data["session"]["user_name"] == "Test User"

    # Assert side effects on session_state
    assert session_state["account_id"] == "ACC123"
    assert session_state["role"] == "customer"
    assert session_state["user_name"] == "Test User"
    assert session_state["pending_action"] is None
    assert session_state["conversation_history"] == []


def test_get_db_view():
    """Test GET /api/db-view calls the database tool with the correct account scope."""
    from backend.main import db

    # Setup database tool mocks
    db.get_accounts = MagicMock(return_value=[{"account_id": "ACC123", "account_name": "Test"}])
    db.get_orders = MagicMock(return_value=[{"order_id": "ORD123"}])
    db.get_tickets = MagicMock(return_value=[{"ticket_id": "TCK123"}])

    # 1. Scoped session
    session_state["account_id"] = "ACC123"
    response = client.get("/api/db-view")
    assert response.status_code == 200
    data = response.json()
    
    db.get_accounts.assert_called_with("ACC123")
    db.get_orders.assert_called_with("ACC123")
    db.get_tickets.assert_called_with("ACC123")
    assert "accounts" in data
    assert "orders" in data
    assert "tickets" in data


def test_chat():
    """Test POST /api/chat invokes the agent and processes response."""
    import json
    from backend.main import agent

    # Setup agent mock
    agent.process_message = MagicMock(return_value={
        "text": "Hello, how can I help you?",
        "pending_action": {"type": "refund", "amount": 100},
        "tool_used": "refund_tool",
        "execution_trace": ["plan", "act"]
    })

    payload = {"message": "Requesting a refund"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    # Read SSE lines and parse them
    lines = [line for line in response.iter_lines() if line]
    
    events = {}
    current_event = None
    for line in lines:
        if line.startswith("event:"):
            current_event = line.split("event:")[1].strip()
        elif line.startswith("data:") and current_event:
            data = json.loads(line.split("data:")[1].strip())
            events[current_event] = data

    assert "trace" in events
    assert "metadata" in events

    metadata = events["metadata"]
    assert metadata["text"] == "Hello, how can I help you?"
    assert metadata["has_pending"] is True
    assert metadata["pending_action"] == {"type": "refund", "amount": 100}
    assert metadata["tool_used"] == "refund_tool"
    assert metadata["execution_trace"] == ["plan", "act"]

    # Verify agent was called with correct arguments
    agent.process_message.assert_called_once()
    args, kwargs = agent.process_message.call_args
    assert kwargs.get("message") == "Requesting a refund"
    assert kwargs.get("account_id") is None
    # Since history was mutated during event generation, we check length
    assert len(kwargs.get("conversation_history")) == 2

    # Verify session state updates
    assert session_state["pending_action"] == {"type": "refund", "amount": 100}
    assert session_state["conversation_history"] == [
        {"role": "user", "content": "Requesting a refund"},
        {"role": "assistant", "content": "Hello, how can I help you?"}
    ]


def test_confirm_action_no_pending():
    """Test POST /api/confirm returns 400 when no pending action exists."""
    session_state["pending_action"] = None
    
    payload = {"confirm": True}
    response = client.post("/api/confirm", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "No pending action to confirm."


def test_confirm_action_cancelled():
    """Test POST /api/confirm cancels the pending action when confirm is False."""
    session_state["pending_action"] = {"type": "refund", "amount": 100}

    payload = {"confirm": False}
    response = client.post("/api/confirm", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Action cancelled. No changes were made."
    assert session_state["pending_action"] is None


def test_confirm_action_approved():
    """Test POST /api/confirm invokes agent with approved=True when confirm is True."""
    from backend.main import agent

    pending_action = {"type": "refund", "amount": 100}
    session_state["pending_action"] = pending_action
    session_state["conversation_history"] = [{"role": "user", "content": "Refund me"}]

    agent.process_message = MagicMock(return_value={
        "text": "Refund processed successfully.",
        "tool_used": "refund_tool",
        "execution_trace": ["execute"]
    })

    payload = {"confirm": True}
    response = client.post("/api/confirm", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "Refund processed successfully."
    assert data["tool_used"] == "refund_tool"
    assert data["execution_trace"] == ["execute"]

    agent.process_message.assert_called_once_with(
        message="Confirmed, please proceed.",
        account_id=None,
        conversation_history=[{"role": "user", "content": "Refund me"}],
        approved=True,
        pending_action=pending_action
    )
    assert session_state["pending_action"] is None
