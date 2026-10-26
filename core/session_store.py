import sqlite3
import json
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agentflow_sessions.db")

class SessionStore:
    """
    Lightweight persistent session store for tracking conversational workflows,
    session checkpoints, and audit trails across runs.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_query TEXT,
                    state_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action TEXT,
                    details TEXT
                )
            """)
            conn.commit()

    def save_state(self, session_id: str, user_query: str, state: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Clean non-serializable elements before storing
            clean_state = {k: v for k, v in state.items() if k != "messages"}
            cursor.execute(
                """
                INSERT INTO sessions (session_id, user_query, state_json)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP,
                    user_query = excluded.user_query,
                    state_json = excluded.state_json
                """,
                (session_id, user_query, json.dumps(clean_state, default=str))
            )
            conn.commit()

    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state_json FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def log_audit_event(self, session_id: str, action: str, details: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO audit_logs (session_id, action, details) VALUES (?, ?, ?)",
                (session_id, action, details)
            )
            conn.commit()

    def get_audit_trail(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, action, details FROM audit_logs WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            return cursor.fetchall()
