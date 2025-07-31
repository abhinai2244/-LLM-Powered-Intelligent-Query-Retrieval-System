import sqlite3

import config
def init_db():
    conn = sqlite3.connect(config.SQLITE_PATH)
    c = conn.cursor()
    c.execute("""
      CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY,
        doc_name TEXT,
        chunk_text TEXT
      )""")
    conn.commit()
    return conn

from pydantic import BaseModel
from typing import List

class QueryInput(BaseModel):
    document_url: str
    questions: List[str]
