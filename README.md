# ParcelPilot Copilot — AI Support Agent

An AI-powered operations and customer support assistant for **ParcelPilot**, a B2B logistics platform. Built as a first-round assessment submission for CalQuity.

---

## 🔗 Links

| | |
|---|---|
| **Hosted App** | [parcelpilot.vercel.app](https://parcelpilot.vercel.app) *(frontend on Vercel)* |
| **Backend API** | Deployed on Render |
| **Submission Notes** | [SUBMISSION.md](./SUBMISSION.md) |

---

## 🧠 What It Does

A full-stack AI agent that helps ParcelPilot support staff (and customers) resolve logistics queries through natural language — with structured data access, policy retrieval, and human-confirmed actions.

- **Dual user context** — Customer-facing and internal operations modes
- **8-node LangGraph pipeline** — Intent → Plan → Retrieve → Resolve → Decide → Approve → Execute → Respond
- **3 agent tools** — Qdrant semantic search, SQLite structured lookup, state-changing actions
- **Source authority ranking** — Customer agreements override SOPs, which override general policies
- **Real-time streaming** — SSE token-by-token streaming to the frontend
- **Confirmation gate** — All state-changing actions require explicit user confirmation

---

## 🏗 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Tailwind CSS |
| Backend | FastAPI (Python) |
| Agent | LangGraph + Google Gemini Flash |
| Vector DB | Qdrant Cloud (`all-MiniLM-L6-v2`) |
| Structured DB | SQLite |
| Hosting | Vercel (frontend) + Render (backend) |

---

## 🚀 Local Setup

### Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt
python database.py --force       # Initialize SQLite DB
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend
```bash
cd frontend/parcelpilot
npm install
npm start                        # http://localhost:3000
```

### Environment Variables

Create `backend/.env`:
```env
QDRANT_URL=<your-qdrant-cluster-url>
QDRANT_API_KEY=<your-qdrant-api-key>
GEMINI_API_KEY=<your-gemini-api-key>
```

Create `frontend/parcelpilot/.env`:
```env
REACT_APP_API_BASE=http://127.0.0.1:8000
```

---

## 🧪 Tests

```bash
.\backend\venv\Scripts\pytest.exe backend/tests/test_api.py -v
```

7 unit tests covering session management, database view, chat streaming, and action confirmation.

---

## 📄 Submission Notes

See [SUBMISSION.md](./SUBMISSION.md) for the full:
- Architecture Note
- Product Note
- Setup & Verification Guide
- AI Tool Usage
