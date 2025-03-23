import sqlite3
import os
import sys
import config

def initialize_db():
    if not os.path.exists(config.DB_PATH):
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                sender TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                summary TEXT DEFAULT NULL,
                email_processed BOOLEAN NOT NULL CHECK (email_processed IN (0, 1)),
                category TEXT DEFAULT NULL
            )
        ''')

        conn.commit()
        conn.close()

def connect_to_db():
    if not os.path.exists(config.DB_PATH):
        initialize_db()
    return sqlite3.connect(config.DB_PATH)

if __name__ == "__main__":
    # Add project root to sys.path to enable importing config when run directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    initialize_db()