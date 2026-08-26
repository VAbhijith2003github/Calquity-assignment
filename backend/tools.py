"""Operational lookup and action tools backed by SQLite."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.database import DATABASE_PATH, initialise_database

BOOLEAN_COLUMNS = {"premium_support", "carrier_fault", "customer_fault"}


class DatabaseTools:
    """SQLite implementation of the existing operational data interface."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = initialise_database(Path(db_path))

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _record(row: sqlite3.Row) -> Dict[str, Any]:
        record = dict(row)
        for column in BOOLEAN_COLUMNS.intersection(record):
            record[column] = bool(record[column])
        return record

    def _list(self, table: str, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query, params = f"SELECT * FROM {table}", ()
        if account_id:
            query += " WHERE account_id = ?"
            params = (account_id,)
        with self._connection() as conn:
            return [self._record(row) for row in conn.execute(query, params).fetchall()]

    def get_accounts(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._list("accounts", account_id)

    def get_orders(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._list("orders", account_id)

    def get_tickets(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._list("tickets", account_id)

    def _lookup(self, table: str, id_column: str, value: str, account_id: Optional[str]) -> Optional[Dict[str, Any]]:
        query, params = f"SELECT * FROM {table} WHERE {id_column} = ?", (value.strip(),)
        if account_id:
            query += " AND account_id = ?"
            params += (account_id,)
        with self._connection() as conn:
            row = conn.execute(query, params).fetchone()
        return self._record(row) if row else None

    def lookup_order_by_id(self, order_id: str, account_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return self._lookup("orders", "order_id", order_id, account_id)

    def lookup_ticket_by_id(self, ticket_id: str, account_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return self._lookup("tickets", "ticket_id", ticket_id, account_id)

    def check_cancellation_fee(self, order_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        order = self.lookup_order_by_id(order_id, account_id)
        if not order:
            return {"allowed": False, "reason": f"Order {order_id} not found or permission denied."}
        if order["status"] == "DELIVERED":
            return {"allowed": False, "reason": "Order has already been delivered."}
        if order["status"] == "PICKED_UP":
            return {"allowed": False, "reason": "Order has already been picked up. Must use return-to-origin workflow instead."}
        if order["status"] != "BOOKED":
            return {"allowed": False, "reason": f"Order cannot be cancelled in state: {order['status']}."}
        requested = order["cancellation_requested_at"] or "2026-08-16 11:00:00"
        try:
            elapsed = (datetime.fromisoformat(str(requested)) - datetime.fromisoformat(str(order["booked_at"]))).total_seconds() / 60
        except (TypeError, ValueError):
            elapsed = 999.0
        fee = 0 if order["account_id"] == "ACCT-001" or elapsed <= 30 else 250
        return {"allowed": True, "fee": fee, "elapsed_minutes": elapsed, "reason": "Cancellation is free under the applicable terms." if not fee else f"An INR 250 cancellation fee applies after {int(elapsed)} minutes."}

    def check_credit_eligibility(self, order_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        order = self.lookup_order_by_id(order_id, account_id)
        if not order:
            return {"eligible": False, "reason": f"Order {order_id} not found or permission denied."}
        if not order["carrier_fault"] or order["customer_fault"]:
            return {"eligible": False, "reason": "No credit: the incident does not meet carrier-fault eligibility."}
        actual = order["pickup_actual_at"] or "2026-08-16 11:00:00"
        try:
            delay = (datetime.fromisoformat(str(actual)) - datetime.fromisoformat(str(order["pickup_window_end"]))).total_seconds() / 3600
        except (TypeError, ValueError):
            delay = 0.0
        if order["account_id"] == "ACCT-002":
            eligible = delay > 4
            return {"eligible": eligible, "credit_amount": 300 if eligible else 0, "delay_hours": delay, "reason": "LumenWorks requires a delay greater than 4 hours."}
        eligible = delay > 2
        amount = min(500, int(float(order["shipment_fee_inr"]) * .1)) if eligible else 0
        return {"eligible": eligible, "credit_amount": amount, "delay_hours": delay, "reason": "Standard policy requires a delay greater than 2 hours."}

    def execute_apply_credit(self, order_id: str, amount: int, reason: str = "Service credit.", account_id: Optional[str] = None) -> str:
        order = self.lookup_order_by_id(order_id, account_id)
        if not order:
            raise PermissionError("Order not found or permission denied.")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        note = f"[System Credit: Applied INR {amount} on {stamp}; {reason}]"
        notes = " | ".join(part for part in (order.get("notes"), note) if part)
        with self._connection() as conn:
            conn.execute("UPDATE orders SET notes = ? WHERE order_id = ?", (notes, order_id))
        return f"Successfully applied service credit of INR {amount} to order {order_id}."

    def execute_cancel_order(self, order_id: str, account_id: Optional[str] = None) -> str:
        if not self.lookup_order_by_id(order_id, account_id):
            raise PermissionError("Order not found or permission denied.")
        with self._connection() as conn:
            conn.execute("UPDATE orders SET status = 'CANCELLED' WHERE order_id = ?", (order_id,))
        return f"Order {order_id} cancelled successfully."

    def execute_escalate_ticket(self, ticket_id: str, reason: str, account_id: Optional[str] = None) -> str:
        ticket = self.lookup_ticket_by_id(ticket_id, account_id)
        if not ticket:
            raise PermissionError("Ticket not found or permission denied.")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        description = f"{ticket.get('description') or ''}\n\n[ESCALATION - {stamp}]: {reason}"
        with self._connection() as conn:
            conn.execute("UPDATE tickets SET assigned_to=?, status=?, description=? WHERE ticket_id=?", ("Engineering Lead", "escalated", description, ticket_id))
        return f"Ticket {ticket_id} escalated successfully to the Engineering Lead."

    def execute_update_ticket_status(self, ticket_id: str, status: str, account_id: Optional[str] = None) -> str:
        if not self.lookup_ticket_by_id(ticket_id, account_id):
            raise PermissionError("Ticket not found or permission denied.")
        with self._connection() as conn:
            conn.execute("UPDATE tickets SET status=? WHERE ticket_id=?", (status, ticket_id))
        return f"Ticket {ticket_id} status updated to '{status}'."
