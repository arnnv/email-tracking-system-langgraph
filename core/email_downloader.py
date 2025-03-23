import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.email_fetcher import get_emails
from core.initialize_db import connect_to_db

from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def download_emails_to_db(count: int) -> None:
    """
    Fetches emails from the specified IMAP server and stores them in the database if they do not already exist.

    Args:
        count (int): The number of emails to fetch.

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
    print(f"  📡 Connecting to server: {IMAP_SERVER}")
    emails = get_emails(IMAP_SERVER, EMAIL, PASSWORD, count=count)
    
    if emails:
        print(f"  ✅ Retrieved {len(emails)} emails from server")
    else:
        print("  ⚠️ No emails retrieved from server")
        return

    new_emails_count = 0
    existing_count = 0
    
    print("  💾 Storing emails in database...")
    for email in emails:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM emails WHERE id = ?', (email["uid"],))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO emails (id, date, sender, email, subject, body, summary, email_processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (email["uid"], email["date"], email["from_name"], email["from_email"], email["subject"], email["body"], None, 0))

            conn.commit()
            new_emails_count += 1
        else:
            existing_count += 1
        conn.close()
    
    print(f"  ✅ Added {new_emails_count} new emails to database" + 
          (f", {existing_count} already existed" if existing_count > 0 else ""))

if __name__ == "__main__":
    # Import the value from main.py if running directly
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    try:
        from main import EMAILS_TO_DOWNLOAD
        print(f"🔍 Using configuration from main.py: {EMAILS_TO_DOWNLOAD} emails")
        download_emails_to_db(EMAILS_TO_DOWNLOAD)
    except ImportError:
        fallback_value = 5
        print(f"⚠️ Configuration not found. Using fallback value: {fallback_value} emails")
        download_emails_to_db(fallback_value)