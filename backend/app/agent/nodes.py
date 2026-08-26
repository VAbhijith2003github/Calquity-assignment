"""
nodes.py
--------
All 8 LangGraph node functions for the ParcelPilot agent pipeline.

Build order followed:
  Step 1: understand → respond (read-only intent parsing)
  Step 2: + gather_evidence
  Step 3: + resolve_sources + make_decision  
  Step 4: + request_approval + execute_action
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from langchain_core.runnables import RunnableConfig

from google import genai
from google.genai import types

from .state import AgentState
from .prompts import UNDERSTAND_PROMPT, DECISION_PROMPT, RESPONSE_PROMPT

logger = logging.getLogger("backend.agent.nodes")

# ── Gemini Client Setup ──────────────────────────────────────────────────────

def _get_gemini_client():
    """Resolves GEMINI_API_KEY from .env and returns a configured client."""
    from dotenv import load_dotenv

    # Walk up from this file's location to find the .env
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            break

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment. Please add it to backend/.env")

    return genai.Client(api_key=api_key)


_gemini_client = None

def get_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = _get_gemini_client()
    return _gemini_client


def _call_gemini(prompt: str) -> str:
    """Calls Gemini 3.6 Flash and returns the text response."""
    client = get_client()
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return response.text


def _call_gemini_text(prompt: str, stream_callback: Optional[Callable[[str], None]] = None) -> str:
    """Calls Gemini 3.6 Flash for a text (non-JSON) response, supporting optional streaming."""
    client = get_client()
    if stream_callback:
        response = client.models.generate_content_stream(
            model="gemini-3.6-flash",
            contents=prompt
        )
        full_text = []
        for chunk in response:
            if chunk.text:
                full_text.append(chunk.text)
                stream_callback(chunk.text)
        return "".join(full_text)
    else:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text


# ── Node 1: Understand Request ───────────────────────────────────────────────

def understand_request(state: AgentState) -> Dict[str, Any]:
    """
    Uses Gemini to parse the user message into structured intent + entities.
    Converts natural language into a structured routing signal.
    """
    messages = state.get("messages", [])
    user_message = messages[-1]["content"] if messages else ""

    logger.info(f"[understand_request] Parsing: '{user_message}'")

    prompt = UNDERSTAND_PROMPT.format(message=user_message)

    try:
        raw = _call_gemini(prompt)
        parsed = json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"[understand_request] LLM parse failed: {e}")
        parsed = {"intent": "general_question", "entities": {}, "requires_action": False}

    intent = parsed.get("intent", "general_question")
    entities = parsed.get("entities", {})
    requires_action = parsed.get("requires_action", False)

    # Clean up null entity values
    entities = {k: v for k, v in entities.items() if v and v != "null"}

    trace = state.get("execution_trace", [])
    trace.append(f"✓ Understood request — intent: {intent}, entities: {entities}")

    logger.info(f"[understand_request] intent={intent}, entities={entities}")

    return {
        "intent": intent,
        "entities": entities,
        "approval_required": requires_action,
        "execution_trace": trace
    }


# ── Node 2: Plan ─────────────────────────────────────────────────────────────

def plan(state: AgentState) -> Dict[str, Any]:
    """
    Deterministic routing table. Decides which tools/data sources are needed.
    No LLM needed — pure Python intent → tool mapping.
    """
    intent = state.get("intent", "general_question")
    trace = state.get("execution_trace", [])

    # Routing table: intent → required_tools
    routing_table = {
        "policy_question":      ["search_documents"],
        "shipment_lookup":      ["get_order"],
        "cancellation_check":   ["get_order", "get_account", "search_documents"],
        "cancellation_action":  ["get_order", "get_account", "search_documents"],
        "credit_check":         ["get_order", "get_account", "search_documents"],
        "credit_action":        ["get_order", "get_account", "search_documents"],
        "case_lookup":          ["get_ticket"],
        "escalation_action":    ["get_ticket", "search_documents"],
        "general_question":     ["search_documents"],
    }

    required_tools = routing_table.get(intent, ["search_documents"])
    trace.append(f"✓ Planned tools required: {required_tools}")
    logger.info(f"[plan] intent={intent} → tools={required_tools}")

    return {
        "operational_data": {"required_tools": required_tools},
        "execution_trace": trace
    }


# ── Node 3: Gather Evidence ───────────────────────────────────────────────────

def gather_evidence(state: AgentState) -> Dict[str, Any]:
    """
    Calls the appropriate data tools (DB lookups + Qdrant search) to collect
    all evidence needed before any decision is made. Agent does NOT answer yet.
    """
    from backend.tools import DatabaseTools
    from backend.retrieval.document_search import search_documents

    db = DatabaseTools()
    entities = state.get("entities", {})
    account_id = state.get("session_account_id")
    required_tools = state.get("operational_data", {}).get("required_tools", [])
    messages = state.get("messages", [])
    user_message = messages[-1]["content"] if messages else ""

    operational_data = {"required_tools": required_tools}
    retrieved_documents = []
    trace = list(state.get("execution_trace", []))

    # ── DB: Fetch Order ──────────────────────────────────────────────────────
    if "get_order" in required_tools and entities.get("order_id"):
        order_id = entities["order_id"].upper()
        order = db.lookup_order_by_id(order_id, account_id)
        if order:
            operational_data["order"] = order
            trace.append(f"✓ Retrieved order {order_id} (status: {order.get('status', 'UNKNOWN')})")
            logger.info(f"[gather_evidence] Order fetched: {order_id}")
        else:
            trace.append(f"✗ Order {order_id} not found or access denied")

    # ── DB: Fetch Account ────────────────────────────────────────────────────
    if "get_account" in required_tools:
        resolve_account_id = account_id or entities.get("account_id")
        if resolve_account_id:
            accounts = db.get_accounts(resolve_account_id)
            if accounts:
                operational_data["account"] = accounts[0]
                trace.append(f"✓ Retrieved account {resolve_account_id} information")
        elif operational_data.get("order"):
            # Infer account_id from the order
            order_acct = operational_data["order"].get("account_id")
            if order_acct:
                accounts = db.get_accounts(order_acct)
                if accounts:
                    operational_data["account"] = accounts[0]
                    trace.append(f"✓ Retrieved account {order_acct} via order")

    # ── DB: Fetch Ticket ─────────────────────────────────────────────────────
    if "get_ticket" in required_tools and entities.get("ticket_id"):
        ticket_id = entities["ticket_id"].upper()
        ticket = db.lookup_ticket_by_id(ticket_id, account_id)
        if ticket:
            operational_data["ticket"] = ticket
            trace.append(f"✓ Retrieved ticket {ticket_id} (status: {ticket.get('status', 'UNKNOWN')})")
        else:
            trace.append(f"✗ Ticket {ticket_id} not found or access denied")

    # ── Qdrant: Semantic Document Search ─────────────────────────────────────
    if "search_documents" in required_tools:
        results = search_documents(
            query=user_message,
            account_id=account_id,
            top_k=3
        )
        retrieved_documents = results
        sources = [r.get("metadata", {}).get("document_name", "Unknown") for r in results]
        trace.append(f"✓ Searched applicable policies — found {len(results)} sources: {sources}")
        logger.info(f"[gather_evidence] Qdrant returned {len(results)} documents")

    return {
        "operational_data": operational_data,
        "retrieved_documents": retrieved_documents,
        "execution_trace": trace
    }


# ── Node 4: Resolve Sources ───────────────────────────────────────────────────

def resolve_sources(state: AgentState) -> Dict[str, Any]:
    """
    Deterministic Python source-precedence resolver.
    Authority levels defined as constants — LLM cannot override these.
    
    Authority hierarchy:
      100 — Customer-specific agreement (highest)
       80 — Current SOP / Product Operations Guide
       20 — Support Policy (current)
        0 — Deprecated documents (ignored entirely)
    """
    retrieved_documents = state.get("retrieved_documents", [])
    account = state.get("operational_data", {}).get("account", {})
    trace = list(state.get("execution_trace", []))

    # Authority mapping rules
    AUTHORITY_MAP = {
        "customer_agreement": 100,
        "enterprise_agreement": 100,
        "service_agreement": 100,
        "sop": 80,
        "operations_guide": 80,
        "support_policy_current": 20,
        "support_policy_deprecated": 0,
    }

    resolved = []
    conflicts = []
    seen_topics = {}

    for doc in retrieved_documents:
        meta = doc.get("metadata", {})
        doc_name = meta.get("document_name", "Unknown")
        doc_type = meta.get("document_type", "").lower()
        retrieval_enabled = meta.get("retrieval_enabled", True)

        # Skip deprecated documents entirely
        if not retrieval_enabled or "deprecated" in doc_type:
            trace.append(f"⊘ Skipped deprecated source: {doc_name}")
            continue

        # Resolve authority level
        authority = AUTHORITY_MAP.get(doc_type, 20)

        # Override if this is account-specific document and matches active account
        if account and meta.get("account_id") == account.get("account_id"):
            authority = 100

        entry = {
            "document": doc_name,
            "document_type": doc_type,
            "authority": authority,
            "content": doc.get("content", ""),
            "section": meta.get("section", "")
        }

        # Conflict detection: same topic answered differently
        topic = meta.get("document_type", doc_name)
        if topic in seen_topics:
            prev = seen_topics[topic]
            if prev["authority"] != authority:
                conflicts.append({
                    "topic": topic,
                    "sources": [prev["document"], doc_name],
                    "resolution": f"Using {prev['document']} (authority {prev['authority']}) over {doc_name} (authority {authority})"
                })
        else:
            seen_topics[topic] = entry

        resolved.append(entry)

    # Sort by authority descending — highest authority first
    resolved.sort(key=lambda x: x["authority"], reverse=True)

    if conflicts:
        trace.append(f"⚠ Source conflicts detected: {len(conflicts)} — resolved by authority precedence")
    trace.append(f"✓ Resolved {len(resolved)} applicable sources (authority order)")

    return {
        "resolved_sources": resolved,
        "conflicts": conflicts,
        "execution_trace": trace
    }


# ── Node 5: Make Decision ─────────────────────────────────────────────────────

def make_decision(state: AgentState) -> Dict[str, Any]:
    """
    Calls Gemini with structured evidence to produce a decision.
    LLM is strictly constrained to use only the supplied evidence.
    """
    messages = state.get("messages", [])
    user_request = messages[-1]["content"] if messages else ""
    operational_data = state.get("operational_data", {})
    resolved_sources = state.get("resolved_sources", [])
    trace = list(state.get("execution_trace", []))

    # Format operational facts
    facts_parts = []
    if "order" in operational_data:
        o = operational_data["order"]
        facts_parts.append(
            f"Order {o.get('order_id')}: status={o.get('status')}, "
            f"carrier={o.get('carrier')}, booked_at={o.get('booked_at')}, "
            f"pickup_window={o.get('pickup_window_start')} to {o.get('pickup_window_end')}, "
            f"pickup_actual={o.get('pickup_actual_at')}, "
            f"carrier_fault={o.get('carrier_fault')}, customer_fault={o.get('customer_fault')}"
        )
    if "account" in operational_data:
        a = operational_data["account"]
        facts_parts.append(
            f"Account {a.get('account_id')} ({a.get('account_name')}): "
            f"plan={a.get('plan')}, premium_support={a.get('premium_support')}"
        )
    if "ticket" in operational_data:
        t = operational_data["ticket"]
        facts_parts.append(
            f"Ticket {t.get('ticket_id')}: status={t.get('status')}, "
            f"subject={t.get('subject')}, assigned_to={t.get('assigned_to')}"
        )

    operational_facts = "\n".join(facts_parts) if facts_parts else "No structured operational data."

    # Format sources
    sources_parts = []
    for src in resolved_sources[:3]:  # Top 3 by authority
        sources_parts.append(
            f"[Authority {src['authority']}] {src['document']} — {src['section']}:\n{src['content'][:500]}"
        )
    sources_text = "\n\n".join(sources_parts) if sources_parts else "No applicable policy documents found."

    prompt = DECISION_PROMPT.format(
        user_request=user_request,
        operational_facts=operational_facts,
        resolved_sources=sources_text
    )

    try:
        raw = _call_gemini(prompt)
        decision = json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"[make_decision] LLM decision failed: {e}")
        decision = {
            "outcome": "insufficient_information",
            "reason": "Could not process the request. Please contact support.",
            "recommended_action": None,
            "action_parameters": {},
            "confidence": "low"
        }

    trace.append(f"✓ Decision reached — outcome: {decision.get('outcome')} (confidence: {decision.get('confidence')})")
    logger.info(f"[make_decision] decision={decision}")

    return {
        "decision": decision,
        "execution_trace": trace
    }


# ── Node 6: Request Approval ──────────────────────────────────────────────────

def request_approval(state: AgentState) -> Dict[str, Any]:
    """
    Prepares the pending_action object and sets approval_required = True.
    The graph will pause here and wait for explicit user confirmation.
    """
    decision = state.get("decision", {})
    entities = state.get("entities", {})
    operational_data = state.get("operational_data", {})
    trace = list(state.get("execution_trace", []))

    action_name = decision.get("recommended_action")
    action_params = decision.get("action_parameters", {})

    # Enrich action parameters with known entities
    if entities.get("order_id"):
        action_params["order_id"] = entities["order_id"]
    if entities.get("ticket_id"):
        action_params["ticket_id"] = entities["ticket_id"]

    pending_action = {
        "name": action_name,
        "parameters": action_params,
        "reason": decision.get("reason", "")
    }

    trace.append(f"⏸ Action '{action_name}' prepared — awaiting user approval")

    return {
        "pending_action": pending_action,
        "approval_required": True,
        "approved": None,
        "execution_trace": trace
    }


# ── Node 7: Execute Action ────────────────────────────────────────────────────

def execute_action(state: AgentState) -> Dict[str, Any]:
    """
    Executes the approved action against the data layer.
    Validates permissions again — never trusts the agent blindly.
    """
    from backend.tools import DatabaseTools

    db = DatabaseTools()
    pending = state.get("pending_action", {})
    account_id = state.get("session_account_id")
    trace = list(state.get("execution_trace", []))

    action_name = pending.get("name")
    params = pending.get("parameters", {})
    result = {"status": "failed", "message": "Unknown action."}

    if action_name == "cancel_shipment" or action_name == "cancel_order":
        order_id = params.get("order_id")
        if order_id:
            # Re-validate: confirm the order still exists and belongs to this account
            order = db.lookup_order_by_id(order_id, account_id)
            if not order:
                result = {"status": "failed", "message": f"Order {order_id} not found or access denied."}
            elif order.get("status") in ("CANCELLED", "DELIVERED"):
                result = {"status": "failed", "message": f"Order {order_id} cannot be cancelled — already {order.get('status')}."}
            else:
                exec_result = db.execute_cancel_order(order_id, account_id=account_id)
                result = {"status": "success", "message": f"Order {order_id} has been cancelled.", "order_id": order_id}
                trace.append(f"✓ Order {order_id} cancelled successfully")

    elif action_name == "apply_credit":
        order_id = params.get("order_id")
        amount = params.get("amount", 0)
        if order_id:
            exec_result = db.execute_apply_credit(order_id, amount=amount, reason=pending.get("reason", "Service credit."), account_id=account_id)
            result = {"status": "success", "message": f"Service credit of INR {amount} applied to order {order_id}.", "order_id": order_id}
            trace.append(f"✓ Service credit INR {amount} applied to order {order_id}")

    elif action_name == "escalate_ticket":
        ticket_id = params.get("ticket_id")
        if ticket_id:
            ticket = db.lookup_ticket_by_id(ticket_id, account_id)
            if not ticket:
                result = {"status": "failed", "message": f"Ticket {ticket_id} not found or access denied."}
            else:
                exec_result = db.execute_escalate_ticket(ticket_id, pending.get("reason", "Escalated by support."), account_id=account_id)
                result = {"status": "success", "message": f"Ticket {ticket_id} escalated to Engineering Lead.", "ticket_id": ticket_id}
                trace.append(f"✓ Ticket {ticket_id} escalated successfully")

    logger.info(f"[execute_action] action={action_name}, result={result}")

    return {
        "action_result": result,
        "execution_trace": trace
    }


# ── Node 8: Generate Response ─────────────────────────────────────────────────

def generate_response(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    Final node. Calls Gemini to convert the structured agent state into a
    clean, user-facing response. Always includes the execution trace.
    """
    messages = state.get("messages", [])
    user_request = messages[-1]["content"] if messages else ""
    decision = state.get("decision", {})
    action_result = state.get("action_result", {})
    trace = state.get("execution_trace", [])
    intent = state.get("intent", "general_question")

    # For simple lookups and policy questions, use structured retrieval + response gen
    decision_text = json.dumps(decision, indent=2) if decision else "N/A"
    action_text = json.dumps(action_result, indent=2) if action_result else "No action taken."
    trace_text = "\n".join(trace) if trace else "No trace available."

    prompt = RESPONSE_PROMPT.format(
        user_request=user_request,
        decision=decision_text,
        action_result=action_text,
        execution_trace=trace_text
    )

    stream_callback = None
    if config:
        stream_callback = config.get("configurable", {}).get("stream_callback")

    try:
        response_text = _call_gemini_text(prompt, stream_callback=stream_callback)
    except Exception as e:
        logger.error(f"[generate_response] Failed: {e}")
        err_msg = str(e).lower()
        if "quota" in err_msg or "exhausted" in err_msg or "429" in err_msg or "503" in err_msg or "unavailable" in err_msg:
            response_text = "⚠️ **API token limit reached.** Please wait a few seconds and try again."
        else:
            if decision:
                response_text = f"{decision.get('reason', 'Unable to process request.')}\n\n**Execution trace:**\n{trace_text}"
            else:
                response_text = "I was unable to process your request. Please contact ParcelPilot support."
        if stream_callback:
            stream_callback(response_text)

    # Tool used tracking
    tool_used = "database_lookup" if intent in ["shipment_lookup", "case_lookup", "cancellation_action", "credit_action", "escalation_action"] else "qdrant_document_search"
    if intent in ["cancellation_check", "credit_check"]:
        tool_used = "database_lookup + qdrant_document_search"

    trace.append("✓ Response generated")

    return {
        "final_response": response_text,
        "execution_trace": trace,
        "tool_used": tool_used  # passed back to main.py for UI badges
    }
