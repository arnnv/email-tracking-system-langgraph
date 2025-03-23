import os
import sys
from core.email_downloader import download_emails_to_db
from models.email import State, Email
from core.utils import connect_to_db

def fetch_unprocessed_emails(state: State) -> State:
    """
    Download new emails and fetch all unprocessed emails from database
    
    Args:
        state: Current application state
        
    Returns:
        Updated application state with unprocessed emails
    """
    # Get state properties
    emails_to_download = state.get("num_emails_to_download")
    debug_mode = state.get("debug_mode", False)
    
    if debug_mode:
        print(f"🔍 Fetch stage with email limit: {emails_to_download}", flush=True)
    
    # If not in state, try to get it from main.py directly
    if emails_to_download is None:
        try:
            # Add the project root to sys.path to allow importing main
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            from main import EMAILS_TO_DOWNLOAD
            emails_to_download = EMAILS_TO_DOWNLOAD
            print("📥 Fallback: Using email limit from main.py configuration")
        except ImportError:
            # Use a fallback value if main.py can't be imported
            emails_to_download = 5
            print("⚠️ Configuration warning: Using default email limit of 5")
        
    print(f"📥 STAGE 1: Downloading {emails_to_download} emails from server...")
    download_emails_to_db(emails_to_download)

    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id, date, sender, email, subject, body, summary FROM emails WHERE email_processed = 0")
        rows = cursor.fetchall()

        emails = []
        for row in rows:
            email = Email(
                id=row[0],
                date=row[1],
                sender=row[2],
                email=row[3],
                subject=row[4],
                body=row[5],
                summary=row[6] if row[6] else ""  
            )
            emails.append(email)

        conn.close()
        
        print(f"✅ Successfully retrieved {len(emails)} unprocessed emails from database")

        # Create a new state preserving all original properties
        new_state = state.copy()
        new_state.update({
            "emails": emails, 
            "classified_emails": {"spam": [], "job": [], "urgent": [], "general": []}, 
            "errors": state.get("errors", []),
            "processing_stage": "summarize"
        })
        return new_state
        
    except Exception as e:
        error_msg = f"Error fetching emails: {str(e)}"
        print(f"❌ Database error: {error_msg}")
        
        if debug_mode:
            import traceback
            print(f"🔍 Fetch error details: {traceback.format_exc()}", flush=True)
            
        # Create a new state preserving all original properties
        new_state = state.copy()
        new_state.update({
            "emails": [], 
            "classified_emails": {"spam": [], "job": [], "urgent": [], "general": []}, 
            "errors": state.get("errors", []) + [error_msg],
            "processing_stage": "end"
        })
        return new_state
