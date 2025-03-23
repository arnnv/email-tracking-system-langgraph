"""
Module for handling user job applications
"""

from jobs.tracker import (
    load_jobs_dataframe, save_jobs_dataframe, update_job_entry
)
from jobs.parser import parse_job_description

def handle_user_job_application(job_description, user_email="user-applied@example.com"):
    """
    Main function to handle a user's job application.
    
    Args:
        job_description: The job description text provided by the user
        user_email: Optional email address to associate with the application (just for record-keeping)
        
    Returns:
        A dictionary with success status and message
    """
    print("\n" + "="*50)
    print("📝 PROCESSING USER JOB APPLICATION")
    print("="*50)
    
    # Parse the job description
    job_details = parse_job_description(job_description)
    
    # Update the jobs.xlsx file
    success, message = update_jobs_with_application(job_details, user_email)
    
    result = {
        "success": success,
        "message": message,
        "company": job_details["company_name"],
        "job_title": job_details["job_title"],
        "status": "Applied"
    }
    
    print(f"Result: {result}")
    print("="*50 + "\n")
    
    return result

def update_jobs_with_application(job_details, user_email="user-applied@example.com"):
    """
    Update the jobs dataframe with the user's job application.
    
    Args:
        job_details: Dictionary containing company_name, job_title, and application_status
        user_email: Optional email address to associate with the application (just for record-keeping)
        
    Returns:
        Boolean indicating success/failure and a status message
    """
    try:
        # Ensure the company name and job title are valid
        if not job_details["company_name"] or job_details["company_name"] == "Unknown Company":
            return False, "Could not identify company name from job description"
        
        if not job_details["job_title"] or job_details["job_title"] == "Unknown Job Title":
            return False, "Could not identify job title from job description"
        
        # Load existing jobs dataframe
        jobs_df = load_jobs_dataframe()
        
        company_name = job_details["company_name"]
        job_title = job_details["job_title"]
        application_status = "pending"  # Default status for user applications
        
        # Update the job entry
        jobs_df, new_entry_created = update_job_entry(
            jobs_df=jobs_df,
            company_name=company_name,
            job_title=job_title,
            application_status=application_status,
            sender_name="User Application",
            sender_email=user_email,
            user_applied=True
        )
        
        # Save the updated dataframe
        save_jobs_dataframe(jobs_df)
        
        if new_entry_created:
            status_message = f"Added new job application for {company_name} - {job_title}"
        else:
            status_message = f"Updated application status for {company_name} - {job_title}"
        
        return True, status_message
        
    except Exception as e:
        error_msg = f"Error updating job application: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg 