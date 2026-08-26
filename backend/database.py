"""SQLite persistence and one-time migration from the assessment workbook."""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BACKEND_DIR / "data" / "parcelpilot.db"
WORKBOOK_CANDIDATES = (
    BACKEND_DIR / "AI Agent Assessment - Candidate Pack" / "ParcelPilot_Assessment_Data.xlsx",
    BACKEND_DIR.parent / "AI Agent Assessment - Candidate Pack" / "ParcelPilot_Assessment_Data.xlsx",
)
SCHEMAS: Dict[str, str] = {
    "accounts": """CREATE TABLE accounts (account_id TEXT PRIMARY KEY, account_name TEXT, plan TEXT, status TEXT, csm TEXT, contract_file TEXT, premium_support INTEGER NOT NULL DEFAULT 0, notes TEXT)""",
    "orders": """CREATE TABLE orders (order_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, carrier TEXT, status TEXT, booked_at TEXT, pickup_window_start TEXT, pickup_window_end TEXT, pickup_actual_at TEXT, shipment_fee_inr REAL, carrier_fault INTEGER NOT NULL DEFAULT 0, customer_fault INTEGER NOT NULL DEFAULT 0, cancellation_requested_at TEXT, notes TEXT, FOREIGN KEY(account_id) REFERENCES accounts(account_id))""",
    "tickets": """CREATE TABLE tickets (ticket_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, created_at TEXT, status TEXT, subject TEXT, description TEXT, channel TEXT, assigned_to TEXT, last_customer_message_at TEXT, historical_resolution TEXT, FOREIGN KEY(account_id) REFERENCES accounts(account_id))""",
}
BOOLEAN_COLUMNS = {"premium_support", "carrier_fault", "customer_fault"}


def _workbook_path() -> Path:
    for path in WORKBOOK_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("ParcelPilot_Assessment_Data.xlsx was not found.")


def _sqlite_value(value: Any, column: str) -> Any:
    if pd.isna(value):
        return None
    if column in BOOLEAN_COLUMNS:
        return int(bool(value))
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def initialise_database(db_path: Path = DATABASE_PATH, force: bool = False) -> Path:
    """Create the SQLite database, seeding it from the workbook on first run."""
    if db_path.exists() and not force:
        return db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for table in SCHEMAS:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        for schema in SCHEMAS.values():
            conn.execute(schema)
        for table in SCHEMAS:
            frame = pd.read_excel(_workbook_path(), sheet_name=table)
            columns = list(frame.columns)
            placeholders = ", ".join("?" for _ in columns)
            rows: Iterable[List[Any]] = ([_sqlite_value(value, column) for column, value in zip(columns, row)] for row in frame.itertuples(index=False, name=None))
            conn.executemany(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", rows)
    return db_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialise ParcelPilot SQLite data from the assessment workbook.")
    parser.add_argument("--force", action="store_true", help="Recreate the SQLite database from the workbook.")
    args = parser.parse_args()
    print(initialise_database(force=args.force))
