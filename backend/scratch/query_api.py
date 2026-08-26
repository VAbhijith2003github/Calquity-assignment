import sys
from pathlib import Path

# Ensure workspace root and backend dir are in sys.path
backend_dir = Path(__file__).resolve().parent.parent
workspace_dir = backend_dir.parent
if str(workspace_dir) not in sys.path:
    sys.path.insert(0, str(workspace_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Force load the .env file to override any existing GEMINI_API_KEY in the process environment
from dotenv import load_dotenv
import os
load_dotenv(backend_dir / ".env", override=True)
print("Active GEMINI_API_KEY (last 8 chars):", os.environ.get("GEMINI_API_KEY", "")[-8:])

from fastapi.testclient import TestClient
from backend.main import app, session_state

client = TestClient(app)

# 1. Update session to Northstar Logistics context
session_state["account_id"] = "ACCT-001"
session_state["role"] = "customer"
session_state["user_name"] = "Northstar Logistics"

query = "A pickup is three hours late because of carrier fault. Should I get a service credit?"
print(f"Sending query to /api/chat: '{query}'\n")

response = client.post("/api/chat", json={"message": query})
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    output_path = Path(__file__).resolve().parent / "response.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=== API CHAT RESPONSE ===\n")
        f.write(f"Response text:\n{data.get('text', '')}\n\n")
        f.write(f"Has Pending Action: {data.get('has_pending')}\n")
        f.write(f"Pending Action Details: {data.get('pending_action')}\n")
        f.write(f"Tool Used: {data.get('tool_used')}\n")
        f.write(f"Execution Trace: {data.get('execution_trace')}\n")
    print(f"Successfully wrote response to {output_path}")
else:
    print(response.text)
