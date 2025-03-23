"""
Job description parsing functionality for the Email Tracking System
"""

from langchain_ollama import ChatOllama
from prompts.job_extraction import get_job_extraction_prompt, parse_key_value_pairs

def parse_job_description(job_description, llm=None):
    """
    Parse a job description to extract company name, job title, and set application status.
    
    Args:
        job_description: The job description text provided by the user
        llm: Language model to use (will create one if not provided)
        
    Returns:
        Dictionary with extracted job details
    """
    if llm is None:
        llm = ChatOllama(model="qwen2.5:7b")
    
    print("🔍 Parsing job description...")
    
    # Use the same prompt as for job emails but with different input
    job_extraction_prompt = get_job_extraction_prompt()
    
    try:
        messages = job_extraction_prompt.format_messages(
            subject="User Job Application", 
            summary=job_description[:1000]  # Use first 1000 chars of job description as summary
        )
        
        result = llm.invoke(messages)
        raw_output = result.content.strip()
        
        print(f"\n🔍 RAW LLM OUTPUT:\n{raw_output}\n")
        
        extracted_details = parse_key_value_pairs(raw_output)
        print(f"🔍 PARSED OUTPUT: {extracted_details}")
        
        if not extracted_details or len(extracted_details) < 2:
            print("⚠️ Incomplete extraction. Using defaults.")
            return {
                "company_name": "Unknown Company",
                "job_title": "Unknown Job Title",
                "application_status": "pending"
            }
        
        company_name = extracted_details.get("Company Name", "Unknown Company")
        job_title = extracted_details.get("Job Title", "Unknown Job Title")
        application_status = "pending"  # Default since user is just applying
        
        print(f"✅ Extracted details: company='{company_name}', title='{job_title}', status='{application_status}'")
        
        return {
            "company_name": company_name,
            "job_title": job_title,
            "application_status": application_status
        }
        
    except Exception as e:
        print(f"❌ Error parsing job description: {str(e)}")
        return {
            "company_name": "Unknown Company",
            "job_title": "Unknown Job Title",
            "application_status": "pending"
        }

def extract_job_details_from_email(llm, email):
    """
    Extract job details from an email using key-value pairs format with the few-shot approach.
    
    Args:
        llm: Language model for extraction
        email: Email to process
        
    Returns:
        Dictionary with extracted job details
    """
    print(f"\n🔄 PROCESSING EMAIL ID {email['id']}", flush=True)

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

            from jobs.tracker import VALID_APPLICATION_STATUSES
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
            retry_count += 1

    return {
        "company_name": "Unknown Company",
        "job_title": "Unknown Job Title",
        "application_status": "pending"
    } 