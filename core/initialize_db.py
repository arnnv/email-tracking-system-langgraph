import sqlite3
import os

def initialize_db():
    if not os.path.exists('emails.db'):
        conn = sqlite3.connect('emails.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                email TEXT NOT NULL,
                sender TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                email_processed BOOLEAN NOT NULL CHECK (email_processed IN (0, 1))
            )
        ''')

        conn.commit()
        conn.close()

def connect_to_db():
    if not os.path.exists('emails.db'):
        initialize_db()
    return sqlite3.connect('emails.db')

if __name__ == "__main__":
    initialize_db()