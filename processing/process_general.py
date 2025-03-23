from models.email import State
from core.utils import connect_to_db

def process_general_emails(state: State) -> dict:
    """
    Mark general emails as processed and update the database
    
    Args:
        state: Current application state
        
    Returns:
        Dictionary with processing results
    """
    general_emails = state['classified_emails']['general']
    processed_ids = []
    errors = []
    
    for email in general_emails:
        try:
            conn = connect_to_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE emails SET email_processed = 1, category = 'general' WHERE id = ?", 
                (email['id'],)
            )
            conn.commit()
            conn.close()
            processed_ids.append(email['id'])
        except Exception as e:
            error_msg = f"Error processing general email ID {email['id']}: {str(e)}"
            errors.append(error_msg)
            
    return {
        "processed_ids": processed_ids,
        "errors": errors
    }
