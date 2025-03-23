from models.email import State
from prompts.summarization_prompt import get_summarization_prompt
import config
from core.utils import connect_to_db

def summarize_emails(state: State) -> State:
    """
    Summarize emails to extract key information for better classification and information extraction
    
    Args:
        state: Current application state
        
    Returns:
        Updated application state with summarized emails
    """
    # Get the language model from state or create a new one
    llm = state.get("model")
    if llm is None:
        llm = config.create_llm()
        state["model"] = llm
    
    debug_mode = state.get("debug_mode", False)
        
    summarized_emails = []
    errors = state.get("errors", [])
    summarization_prompt = get_summarization_prompt()

    email_count = len(state['emails'])
    print(f"📝 STAGE 2: Summarizing {email_count} emails...")
    for i, email in enumerate(state["emails"], 1):
        try:
            messages = summarization_prompt.format_messages(
                subject=email["subject"], 
                body=email["body"], 
                sender=email["sender"]
            )
            result = llm.invoke(messages)
            email["summary"] = result.content.strip()
            
            # Save summary to database
            try:
                conn = connect_to_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE emails SET summary = ? WHERE id = ?", 
                              (email["summary"], email["id"]))
                conn.commit()
                conn.close()
                print(f"  💾 [{i}/{email_count}] Saved summary to database for email ID {email['id']}")
                
                if debug_mode:
                    print(f"  🔍 Summary for email {email['id']}: {email['summary'][:100]}...", flush=True)
            except Exception as e:
                db_error = f"Error saving summary to database for email ID {email['id']}: {str(e)}"
                errors.append(db_error)
                print(f"  ❌ {db_error}")
            
            summarized_emails.append(email)
            print(f"  ✅ [{i}/{email_count}] Summarized email from {email['sender']}")
        except Exception as e:
            error_msg = f"Error summarizing email ID {email['id']}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ [{i}/{email_count}] {error_msg}")
            
            if debug_mode:
                import traceback
                print(f"  🔍 Error details: {traceback.format_exc()}", flush=True)
                
            email["summary"] = "Failed to summarize email content."
            summarized_emails.append(email)

    print(f"✅ Completed summarization of {len(summarized_emails)} emails")
    return {
        "emails": summarized_emails, 
        "classified_emails": state["classified_emails"], 
        "errors": errors,
        "processing_stage": "classify",
        "model": state.get("model"),
        "debug_mode": state.get("debug_mode", False),
        "num_emails_to_download": state.get("num_emails_to_download")
    }
