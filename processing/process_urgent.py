from models.email import State
from core.utils import connect_to_db
from plyer import notification

def process_urgent_emails(state: State) -> dict:
    """
    Process urgent emails, update DB, and send desktop notifications.
    
    Args:
        state: Current application state
        
    Returns:
        Dictionary with processed IDs and any errors
    """
    local_errors = []
    processed_ids = []
    urgent_emails = state["classified_emails"]["urgent"]
    print(f"Processing {len(urgent_emails)} urgent emails...")

    try:
        for email in urgent_emails:
            try:
                conn = connect_to_db()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE emails SET email_processed = 1, category = 'urgent' WHERE id = ?", 
                    (email["id"],)
                )
                conn.commit()
                conn.close()
                processed_ids.append(email["id"])

                # Send desktop notification for urgent emails
                notification_title = f"Urgent Email from {email['sender']}"
                notification_message = f"Subject: {email['subject']}\n{email['summary'][:200]}"  
                notification.notify(
                    title=notification_title,
                    message=notification_message,
                    app_name="Email Filter",
                    timeout=5  
                )
            except Exception as e:
                error_msg = f"Error processing urgent email ID {email['id']}: {str(e)}"
                local_errors.append(error_msg)
    except Exception as e:
        local_errors.append(f"Error processing urgent emails: {str(e)}")

    return {"processed_ids": processed_ids, "errors": local_errors}
