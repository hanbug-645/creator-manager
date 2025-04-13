import sqlite3
from datetime import datetime
from enum import Enum
from typing import Optional

class EmailAction(str, Enum):
    NEGOTIATION = "Negotiation"
    REJECTED = "Rejected"
    ASSET_PROVIDED = "Asset Provided"

    @classmethod
    def from_str(cls, value: str) -> 'EmailAction':
        try:
            return cls(value)
        except ValueError:
            return cls.NEGOTIATION

class EmailDatabase:
    def __init__(self, db_path: str = "emails.db"):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    action TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_email(self, title: str, action: EmailAction, timestamp: Optional[datetime] = None):
        if timestamp is None:
            timestamp = datetime.now()
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO emails (title, timestamp, action) VALUES (?, ?, ?)",
                (title, timestamp.isoformat(), action.value)
            )
            conn.commit()

    def get_all_emails(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emails ORDER BY timestamp DESC")
            return cursor.fetchall()

    def get_latest_emails(self, limit: int = 3):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, timestamp, action FROM emails ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return [
                {
                    'id': row[0],
                    'title': row[1],
                    'timestamp': datetime.fromisoformat(row[2]),
                    'action': EmailAction.from_str(row[3])
                }
                for row in cursor.fetchall()
            ]

    def get_emails_by_action(self, action: EmailAction):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM emails WHERE action = ? ORDER BY timestamp DESC",
                (action.value,)
            )
            return cursor.fetchall()

    def update_email_action(self, email_id: int, new_action: EmailAction):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE emails SET action = ? WHERE id = ?",
                (new_action.value, email_id)
            )
            conn.commit()
