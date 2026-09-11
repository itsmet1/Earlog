"""
EarLog - db.py

Shared SQLite helper. Creates the events table if it doesn't exist
and provides a single get_connection() function used by both the
watcher and the API.
"""

import sqlite3
import sys
from pathlib import Path


def _base_dir() -> Path:
    """
    Returns the folder the database should live in.
    - Normal 'python api.py' run: the folder this script is in.
    - Bundled PyInstaller .exe: the folder the .exe itself sits in
      (NOT the temporary extraction folder PyInstaller uses, which
      gets wiped between runs and would lose your data every time).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


DB_PATH = _base_dir() / "earlog.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL CHECK (event_type IN ('connected', 'disconnected')),
            device_mac TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialised at {DB_PATH}")