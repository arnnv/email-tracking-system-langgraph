from models.email import State
from core.utils import connect_to_db

def process_spam_emails(state: State) -> dict:
    """
    Mark spam emails as processed and update the database
    
    Args:
        state: Current application state
        
    Returns:
        Dictionary with processing results
    """
    spam_emails = state['classified_emails']['spam']
    processed_ids = []
    errors = []
    
    for email in spam_emails:
        try:
            conn = connect_to_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE emails SET email_processed = 1, category = 'spam' WHERE id = ?", 
                (email['id'],)
            )
            conn.commit()
            conn.close()
            processed_ids.append(email['id'])
        except Exception as e:
            error_msg = f"Error processing spam email ID {email['id']}: {str(e)}"
            errors.append(error_msg)
            
    return {
        "processed_ids": processed_ids,
        "errors": errors
    }
