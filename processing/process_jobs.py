import os
import pandas as pd
import traceback
from models.email import State
from jobs.processor import process_job_emails
from core.utils import connect_to_db
import config

# For backward compatibility, re-export these
from jobs.tracker import JOB_COLUMNS, VALID_APPLICATION_STATUSES
from prompts.job_extraction import get_job_extraction_prompt, parse_key_value_pairs

def extract_job_details(llm, email):
    """
    Extract job details from an email using key-value pairs format with the few-shot approach.
    
    Args:
        llm: Language model for extraction
        email: Email to process
        
    Returns:
        Dictionary with extracted job details
    """
    print(f"\n🔄 PROCESSING EMAIL ID {email['id']}", flush=True)

    # Check if LLM is available
    if llm is None:
        print(f"❌ LLM not available for email ID {email['id']}", flush=True)
        return {
            "company_name": "Unknown Company",
            "job_title": "Unknown Job Title",
            "application_status": "pending"
        }

    subject = str(email.get("subject", "")).strip()
    summary = str(email.get("summary", "")).strip()

    print(f"📧 EMAIL SUBJECT: {subject[:50]}...", flush=True)
    print(f"📝 EMAIL SUMMARY: {summary[:50]}...", flush=True)

    max_retries = 2
    retry_count = 0
    job_extraction_prompt = get_job_extraction_prompt()

    while retry_count <= max_retries:
        try:
            print(f"🔄 Sending request to LLM for email ID {email['id']} (Attempt {retry_count + 1})", flush=True)

            messages = job_extraction_prompt.format_messages(
                subject=subject, 
                summary=summary  
            )

            result = llm.invoke(messages)
            raw_output = result.content.strip()

            print(f"\n🔍 RAW LLM OUTPUT for Email ID {email['id']}:\n{raw_output}\n", flush=True)

            extracted_details = parse_key_value_pairs(raw_output)

            print(f"🔍 PARSED OUTPUT: {extracted_details}", flush=True)

            if not extracted_details or len(extracted_details) < 2:
                if retry_count < max_retries:
                    print("⚠️ Incomplete extraction. Retrying...", flush=True)
                    retry_count += 1
                    continue
                else:
                    print(f"⚠️ Failed to extract complete details after {max_retries} attempts. Using defaults.", flush=True)
                    return {
                        "company_name": "Unknown Company",
                        "job_title": "Unknown Job Title",
                        "application_status": "pending"
                    }

            company_name = extracted_details.get("Company Name", "Unknown Company")
            job_title = extracted_details.get("Job Title", "Unknown Job Title")
            application_status = extracted_details.get("Application Status", "pending").strip().lower()

            if job_title is None or job_title.strip() == "":
                job_title = "Unknown Job Title"

            if application_status not in VALID_APPLICATION_STATUSES:
                print(f"⚠️ Invalid application_status '{application_status}'. Defaulting to 'pending'.", flush=True)
                application_status = "pending"

            print(f"✅ Final extracted details: company='{company_name}', title='{job_title}', status='{application_status}'", flush=True)

            return {
                "company_name": company_name,
                "job_title": job_title,
                "application_status": application_status
            }

        except Exception as e:
            print(f"❌ Error processing email ID {email['id']}: {str(e)}", flush=True)
            print(f"❌ TRACEBACK: {traceback.format_exc()}", flush=True)
            retry_count += 1

    return {
        "company_name": "Unknown Company",
        "job_title": "Unknown Job Title",
        "application_status": "pending"
    }

def update_jobs_dataframe(jobs_df, email, job_details):
    """
    Update the jobs dataframe with the extracted job details.
    
    Args:
        jobs_df: DataFrame containing job applications
        email: Email to process
        job_details: Extracted job details dictionary
        
    Returns:
        Updated jobs DataFrame
    """
    company_name = job_details["company_name"]
    job_title = job_details["job_title"]
    application_status = job_details["application_status"]

    print(f"🔄 Updating jobs dataframe for email ID {email['id']} with: {company_name} - {job_title}", flush=True)

    # Find existing entry by company name and job title (case-insensitive)
    existing_entry = jobs_df[
        (jobs_df["company_name"].str.lower() == company_name.lower()) & 
        (jobs_df["job_title"].str.lower() == job_title.lower())
    ]

    if not existing_entry.empty:
        print(f"🔍 Found existing entry for {company_name} - {job_title}", flush=True)
        
        # Preserve user_applied status if it's already True
        user_applied = existing_entry["user_applied"].iloc[0]
        
        # Only update application status if the user hasn't applied or if new status is more advanced
        if not user_applied or should_update_status(existing_entry["application_status"].iloc[0], application_status):
            jobs_df.loc[existing_entry.index, "application_status"] = application_status
            print(f"✅ Updated job application: {company_name} - {job_title} ({application_status})", flush=True)
        else:
            print("ℹ️ Keeping existing application status due to user applied flag", flush=True)
            
        # Update source email info if we have better information
        jobs_df.loc[existing_entry.index, "id"] = email["id"]
        jobs_df.loc[existing_entry.index, "sender_name"] = email.get("sender", "Unknown")
        jobs_df.loc[existing_entry.index, "sender_email"] = email.get("email", "unknown@example.com")
    else:
        print(f"🔍 No existing entry found for {company_name} - {job_title}", flush=True)

        new_entry = {
            "id": email["id"],
            "sender_name": email.get("sender", "Unknown"),
            "sender_email": email.get("email", "unknown@example.com"),
            "company_name": company_name,
            "job_title": job_title,
            "application_status": application_status,
            "user_applied": False  
        }
        jobs_df = pd.concat([jobs_df, pd.DataFrame([new_entry])], ignore_index=True)
        print(f"➕ Added new job application: {company_name} - {job_title} ({application_status})", flush=True)

    return jobs_df

def should_update_status(current_status, new_status):
    """
    Determine if the application status should be updated based on priority.
    
    Args:
        current_status: Current application status
        new_status: New application status
        
    Returns:
        Boolean indicating if the status should be updated
    """
    status_priority = {
        "pending": 0,
        "interview scheduled": 1,
        "accepted": 2,
        "rejected": 3
    }
    
    # Default to lowest priority if status is unknown
    current_priority = status_priority.get(current_status, -1)
    new_priority = status_priority.get(new_status, -1)
    
    # Update if new status has higher priority
    return new_priority > current_priority

def process_job_emails(state: State) -> dict:
    """
    Process job emails, extract job details, and update the database
    
    Args:
        state: Current application state
        
    Returns:
        Dictionary with processing results
    """
    local_errors = []
    processed_ids = []
    
    # Get the language model from state or create a new one
    llm = state.get("model")
    debug_mode = state.get("debug_mode", False)
    
    if llm is None:
        try:
            llm = config.create_llm()
            print(f"🔄 Creating new language model: {config.LLM_MODEL}", flush=True)
        except Exception as model_error:
            error_msg = f"❌ Model initialization error: {str(model_error)}"
            print(error_msg, flush=True)
            if debug_mode:
                print(f"❌ TRACEBACK: {traceback.format_exc()}", flush=True)
            llm = None
            local_errors.append(error_msg)

    print(f"🔍 State keys: {state.keys()}", flush=True)

    if "classified_emails" not in state or "job" not in state["classified_emails"]:
        print("❌ Missing classified_emails or job key in state", flush=True)
        return {"processed_ids": [], "errors": ["Missing classified_emails or job key in state"]}

    job_emails = state["classified_emails"]["job"]
    print(f"Processing {len(job_emails)} job emails...", flush=True)

    if os.path.exists("jobs.xlsx"):
        print("📂 Loading existing jobs.xlsx file", flush=True)
        jobs_df = pd.read_excel("jobs.xlsx", engine="openpyxl")
        
        # Print job application stats
        user_applied_count = jobs_df["user_applied"].sum()
        print(f"📊 Current job tracker: {len(jobs_df)} total jobs, {user_applied_count} applications", flush=True)
    else:
        print("📂 Creating new jobs dataframe", flush=True)
        jobs_df = pd.DataFrame(columns=JOB_COLUMNS)

    try:
        print("🔄 Connecting to database", flush=True)
        conn = connect_to_db()
        cursor = conn.cursor()

        for email in job_emails:
            print(f"\n==== PROCESSING EMAIL ID {email['id']} ====", flush=True)
            try:
                job_details = extract_job_details(llm, email)
                jobs_df = update_jobs_dataframe(jobs_df, email, job_details)

                cursor.execute("UPDATE emails SET email_processed = 1, category = 'job' WHERE id = ?", 
                               (email["id"],))
                processed_ids.append(email["id"])
                print(f"✅ Email ID {email['id']} successfully processed", flush=True)

            except Exception as llm_error:
                error_msg = f"❌ ERROR parsing job email ID {email['id']}: {llm_error}"
                print(error_msg, flush=True)
                
                if debug_mode:
                    print(f"❌ TRACEBACK: {traceback.format_exc()}", flush=True)
                    
                local_errors.append(f"Error parsing job email ID {email['id']}: {str(llm_error)}")

        conn.commit()
        conn.close()
        jobs_df.to_excel("jobs.xlsx", index=False, engine="openpyxl")
        
        # Print updated stats
        user_applied_count = jobs_df["user_applied"].sum()
        print(f"📊 Updated job tracker: {len(jobs_df)} total jobs, {user_applied_count} applications", flush=True)
        print("📁 Updated jobs.xlsx", flush=True)

    except Exception as e:
        error_msg = f"❌ Error in process_job_emails: {str(e)}"
        print(error_msg, flush=True)
        
        if debug_mode:
            print(f"❌ TRACEBACK: {traceback.format_exc()}", flush=True)
            
        local_errors.append(f"Error processing job emails: {str(e)}")

    return {"processed_ids": processed_ids, "errors": local_errors}
