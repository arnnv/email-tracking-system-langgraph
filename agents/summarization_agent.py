"""
Email Summarization Agent
Responsible for extracting key information from email content.
"""
from models.email import State
from prompts.summarization_prompt import get_summarization_prompt
import config
from core.utils import connect_to_db

class SummarizationAgent:
    """
    Agent for summarizing email content to extract key information
    for better classification and information extraction.
    """
    
    def __init__(self, model=None, debug_mode=False):
        """
        Initialize the summarization agent
        
        Args:
            model: Language model to use for summarization
            debug_mode: Whether to enable verbose logging
        """
        self.model = model if model else config.create_llm()
        self.debug_mode = debug_mode
        self.summarization_prompt = get_summarization_prompt()
    
    def process_email(self, email):
        """
        Process a single email and generate a summary
        
        Args:
            email: Email dict containing subject, body, sender
            
        Returns:
            Updated email dict with summary added
            
        Raises:
            Exception: If summarization fails
        """
        messages = self.summarization_prompt.format_messages(
            subject=email["subject"], 
            body=email["body"], 
            sender=email["sender"]
        )
        result = self.model.invoke(messages)
        email["summary"] = result.content.strip()
        return email
    
    def save_summary_to_db(self, email):
        """
        Save email summary to the database
        
        Args:
            email: Email dict with generated summary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = connect_to_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE emails SET summary = ? WHERE id = ?", 
                          (email["summary"], email["id"]))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if self.debug_mode:
                import traceback
                print(f"  🔍 Database error details: {traceback.format_exc()}", flush=True)
            return False
    
    def process(self, state: State) -> State:
        """
        Process all emails in the state and generate summaries
        
        Args:
            state: Current application state
            
        Returns:
            Updated application state with summarized emails
        """
        summarized_emails = []
        errors = state.get("errors", [])
        
        email_count = len(state['emails'])
        print(f"📝 STAGE 2: Summarizing {email_count} emails...")
        
        for i, email in enumerate(state["emails"], 1):
            try:
                # Process the email to get a summary
                updated_email = self.process_email(email)
                
                # Save summary to database
                db_success = self.save_summary_to_db(updated_email)
                if db_success:
                    print(f"  💾 [{i}/{email_count}] Saved summary to database for email ID {updated_email['id']}")
                    
                    if self.debug_mode:
                        print(f"  🔍 Summary for email {updated_email['id']}: {updated_email['summary'][:100]}...", flush=True)
                else:
                    db_error = f"Error saving summary to database for email ID {updated_email['id']}"
                    errors.append(db_error)
                    print(f"  ❌ {db_error}")
                
                summarized_emails.append(updated_email)
                print(f"  ✅ [{i}/{email_count}] Summarized email from {updated_email['sender']}")
                
            except Exception as e:
                error_msg = f"Error summarizing email ID {email['id']}: {str(e)}"
                errors.append(error_msg)
                print(f"  ❌ [{i}/{email_count}] {error_msg}")
                
                if self.debug_mode:
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
            "model": self.model,
            "debug_mode": self.debug_mode,
            "num_emails_to_download": state.get("num_emails_to_download")
        }

def summarize_emails(state: State) -> State:
    """
    Wrapper function for the SummarizationAgent to maintain compatibility
    with the existing workflow
    
    Args:
        state: Current application state
        
    Returns:
        Updated application state with summarized emails
    """
    # Use the model from state or create a new one
    model = state.get("model")
    if model is None:
        model = config.create_llm()
        state["model"] = model
    
    debug_mode = state.get("debug_mode", False)
    
    # Create and run the agent
    agent = SummarizationAgent(model=model, debug_mode=debug_mode)
    return agent.process(state) 