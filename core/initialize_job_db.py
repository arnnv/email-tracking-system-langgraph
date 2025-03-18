import sqlite3
import os

def initialize_job_db():
    if not os.path.exists('jobs.db'):
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            company_name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            application_status TEXT NOT NULL,
            user_applied BOOLEAN NOT NULL CHECK (user_applied IN (0, 1))
            )
        ''')

        conn.commit()
        conn.close()

def connect_to_jobs_db():
    if not os.path.exists('jobs.db'):
        initialize_job_db()
    return sqlite3.connect('jobs.db')

if __name__ == "__main__":
    initialize_job_db()
