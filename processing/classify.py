from models.email import State
from prompts.classification_prompt import get_classification_prompt
import config

def enforce_single_category(category_text):
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

def classify_emails(state: State) -> State:
    """
    Classify each email into one of four categories: spam, job, urgent, or general.
    Using FewShotChatMessagePromptTemplate with email summaries for improved accuracy.
    
    Args:
        state: Current application state
        
    Returns:
        Updated application state with classified emails
    """
    # Get the language model from state or create a new one
    llm = state.get("model")
    if llm is None:
        llm = config.create_llm()
        state["model"] = llm
    
    debug_mode = state.get("debug_mode", False)
        
    classified_emails = {"spam": [], "job": [], "urgent": [], "general": []}
    errors = state.get("errors", [])
    classification_prompt = get_classification_prompt()

    email_count = len(state["emails"])
    print(f"🔍 STAGE 3: Classifying {email_count} emails...")
    
    for i, email in enumerate(state["emails"], 1):
        try:
            messages = classification_prompt.format_messages(
                subject=email["subject"], 
                summary=email["summary"],  
                sender=email["sender"]
            )
            result = llm.invoke(messages)
            raw_category = result.content.strip().lower()

            category = enforce_single_category(raw_category)

            if raw_category != category:
                print(f"  ⚠️ [{i}/{email_count}] Corrected ambiguous classification: '{raw_category}' → '{category}'")
            else:
                print(f"  ✅ [{i}/{email_count}] Classified as '{category}': {email['subject'][:30]}...")
            
            if debug_mode:
                print(f"  🔍 Classification details for email {email['id']}:")
                print(f"      Subject: {email['subject']}")
                print(f"      Raw classification: '{raw_category}'")
                print(f"      Final category: '{category}'")

            classified_emails[category].append(email)

        except Exception as e:
            error_msg = f"Error classifying email ID {email['id']}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ [{i}/{email_count}] {error_msg}")
            
            if debug_mode:
                import traceback
                print(f"  🔍 Error details: {traceback.format_exc()}", flush=True)
                
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
        "model": state.get("model"),
        "debug_mode": state.get("debug_mode", False),
        "num_emails_to_download": state.get("num_emails_to_download")
    }
