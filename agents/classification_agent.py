"""
Email Classification Agent
Responsible for categorizing emails into spam, job, urgent, or general.
"""
from models.email import State
from prompts.classification_prompt import get_classification_prompt
import config

class ClassificationAgent:
    """
    Agent for classifying emails into specified categories
    using LLM-based classification.
    """
    
    def __init__(self, model=None, debug_mode=False):
        """
        Initialize the classification agent
        
        Args:
            model: Language model to use for classification
            debug_mode: Whether to enable verbose logging
        """
        self.model = model if model else config.create_llm()
        self.debug_mode = debug_mode
        self.classification_prompt = get_classification_prompt()
    
    def enforce_single_category(self, category_text):
        """
        Ensure only a single category word is returned
        
        Args:
            category_text: Raw category text from LLM
            
        Returns:
            Cleaned category value
        """
        clean_text = category_text.lower().strip()

        if clean_text == "spam" or clean_text == "job" or clean_text == "urgent" or clean_text == "general":
            return clean_text

        words = clean_text.split()
        for category in ["spam", "job", "urgent", "general"]:
            if category in words:
                return category

        return "general"
    
    def classify_email(self, email):
        """
        Classify a single email into a category
        
        Args:
            email: Email dict containing subject, summary, sender
            
        Returns:
            Category string: 'spam', 'job', 'urgent', or 'general'
            
        Raises:
            Exception: If classification fails
        """
        messages = self.classification_prompt.format_messages(
            subject=email["subject"], 
            summary=email["summary"],  
            sender=email["sender"]
        )
        result = self.model.invoke(messages)
        raw_category = result.content.strip().lower()
        
        return self.enforce_single_category(raw_category), raw_category
    
    def process(self, state: State) -> State:
        """
        Process all emails in the state and classify them into categories
        
        Args:
            state: Current application state
            
        Returns:
            Updated application state with classified emails
        """
        classified_emails = {"spam": [], "job": [], "urgent": [], "general": []}
        errors = state.get("errors", [])

        email_count = len(state["emails"])
        print(f"🔍 STAGE 3: Classifying {email_count} emails...")
        
        for i, email in enumerate(state["emails"], 1):
            try:
                # Classify the email
                category, raw_category = self.classify_email(email)

                # Log classification results
                if raw_category != category:
                    print(f"  ⚠️ [{i}/{email_count}] Corrected ambiguous classification: '{raw_category}' → '{category}'")
                else:
                    print(f"  ✅ [{i}/{email_count}] Classified as '{category}': {email['subject'][:30]}...")
                
                if self.debug_mode:
                    print(f"  🔍 Classification details for email {email['id']}:")
                    print(f"      Subject: {email['subject']}")
                    print(f"      Raw classification: '{raw_category}'")
                    print(f"      Final category: '{category}'")

                # Add email to the appropriate category
                classified_emails[category].append(email)

            except Exception as e:
                error_msg = f"Error classifying email ID {email['id']}: {str(e)}"
                errors.append(error_msg)
                print(f"  ❌ [{i}/{email_count}] {error_msg}")
                
                if self.debug_mode:
                    import traceback
                    print(f"  🔍 Error details: {traceback.format_exc()}", flush=True)
                    
                # Default to general category on error
                classified_emails["general"].append(email)
        
        # Print classification summary
        print("\n📊 Classification results:")
        for category, emails in classified_emails.items():
            print(f"  • {category.capitalize()}: {len(emails)} emails")

        return {
            "emails": state["emails"], 
            "classified_emails": classified_emails, 
            "errors": errors,
            "processing_stage": "process_parallel",
            "model": self.model,
            "debug_mode": self.debug_mode,
            "num_emails_to_download": state.get("num_emails_to_download")
        }

def classify_emails(state: State) -> State:
    """
    Wrapper function for the ClassificationAgent to maintain compatibility
    with the existing workflow
    
    Args:
        state: Current application state
        
    Returns:
        Updated application state with classified emails
    """
    # Use the model from state or create a new one
    model = state.get("model")
    if model is None:
        model = config.create_llm()
        state["model"] = model
    
    debug_mode = state.get("debug_mode", False)
    
    # Create and run the agent
    agent = ClassificationAgent(model=model, debug_mode=debug_mode)
    return agent.process(state) 