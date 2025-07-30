import sqlite3
from contextlib import contextmanager
import os

class Database:
    def __init__(self, db_name: str = os.getenv("DB_PATH", "policy.db")):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with required tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    type TEXT NOT NULL,
                    is_known BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Queries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    query_text TEXT NOT NULL,
                    answer TEXT,
                    rationale TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            """)
            conn.commit()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()

    def save_document(self, url: str, doc_type: str, is_known: bool = True):
        """Save document metadata to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO documents (url, type, is_known) VALUES (?, ?, ?)",
                (url, doc_type, is_known)
            )
            conn.commit()
            return cursor.lastrowid

    def save_query(self, document_id: int, query_text: str, answer: str, rationale: str):
        """Save query and response to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO queries (document_id, query_text, answer, rationale) VALUES (?, ?, ?, ?)",
                (document_id, query_text, answer, rationale)
            )
            conn.commit()

    def get_document(self, doc_id: int):
        """Retrieve document metadata by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            return cursor.fetchone()