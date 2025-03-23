"""
Module for processing job emails
"""

import sqlite3
import traceback
from models.email import State
from langchain_ollama import ChatOllama
from jobs.parser import extract_job_details_from_email
from jobs.tracker import load_jobs_dataframe, save_jobs_dataframe, update_job_entry

def process_job_emails(state: State, llm=None) -> dict:
    """
    Process job-related emails, update the DB, and track job applications in jobs.xlsx.
    
    Args:
        state: Current application state
        llm: Language model for job extraction (will create one if not provided)
        
    Returns:
        Dictionary with processed IDs and any errors
    """
    # Use provided LLM or create a new one
    if llm is None:
        llm = ChatOllama(model="qwen2.5:7b")
        
    local_errors = []
    processed_ids = []

    print(f"🔍 State keys: {state.keys()}", flush=True)

    if "classified_emails" not in state or "job" not in state["classified_emails"]:
        print("❌ Missing classified_emails or job key in state", flush=True)
        return {"processed_ids": [], "errors": ["Missing classified_emails or job key in state"]}

    job_emails = state["classified_emails"]["job"]
    print(f"Processing {len(job_emails)} job emails...", flush=True)

    # Load the jobs dataframe
    jobs_df = load_jobs_dataframe()

    try:
        print("🔄 Connecting to database", flush=True)
        conn = sqlite3.connect('emails.db')
        cursor = conn.cursor()

        for email in job_emails:
            print(f"\n==== PROCESSING EMAIL ID {email['id']} ====", flush=True)
            try:
                # Extract job details using LLM
                job_details = extract_job_details_from_email(llm, email)
                
                # Update job tracker with extracted information
                jobs_df, _ = update_job_entry(
                    jobs_df=jobs_df,
                    company_name=job_details["company_name"],
                    job_title=job_details["job_title"],
                    application_status=job_details["application_status"],
                    email_id=email["id"],
                    sender_name=email.get("sender", "Unknown"),
                    sender_email=email.get("email", "unknown@example.com"),
                    user_applied=False
                )

                # Mark email as processed in database
                cursor.execute("UPDATE emails SET email_processed = 1, category = 'job' WHERE id = ?", 
                               (email["id"],))
                processed_ids.append(email["id"])
                print(f"✅ Email ID {email['id']} successfully processed", flush=True)

            except Exception as llm_error:
                error_msg = f"Error parsing job email ID {email['id']}: {str(llm_error)}"
                print(f"❌ ERROR: {error_msg}", flush=True)
                print(f"❌ TRACEBACK: {traceback.format_exc()}", flush=True)
                local_errors.append(error_msg)

        # Commit database changes and save job tracker
        conn.commit()
        conn.close()
        save_jobs_dataframe(jobs_df)

    except Exception as e:
        error_msg = f"Error in process_job_emails: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        print(f"❌ TRACEBACK: {traceback.format_exc()}", flush=True)
        local_errors.append(error_msg)

    return {"processed_ids": processed_ids, "errors": local_errors} 