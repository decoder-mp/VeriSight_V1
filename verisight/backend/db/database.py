import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "verisight.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with users and verifications tables."""
    if not os.path.exists(DB_PATH):
        conn = get_db()
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print("[DB] Database created and schema loaded.")
    else:
        print("[DB] Database already exists.")

if __name__ == "__main__":
    init_db()
