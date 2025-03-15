import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pprint import pprint
from core.email_fetcher import get_emails
from core.initialize_db import connect_to_db

from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def email_fetcher_agent(count: int = 10) -> None:
    """
    Fetches emails from the specified IMAP server and stores them in the database if they do not already exist.

    Args:
        count (int, optional): The number of emails to fetch. Defaults to 10.

    Returns:
        None

    The function performs the following steps:
    1. Fetches emails using the `get_emails` function.
    2. Iterates through the fetched emails and prints each email.
    3. Connects to the database.
    4. Checks if the email already exists in the database by its unique ID.
    5. If the email does not exist, inserts the email details into the database.
    6. Commits the transaction and closes the database connection.
    """
    emails = get_emails(IMAP_SERVER, EMAIL, PASSWORD)

    for email in emails:
        # pprint(email)

        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM emails WHERE id = ?', (email["uid"],))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO emails (id, date, sender, email, subject, body, email_processed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (email["uid"], email["date"], email["from_name"], email["from_email"], email["subject"], email["body"], 0))

            conn.commit()
        conn.close()

if __name__ == "__main__":
    email_fetcher_agent()