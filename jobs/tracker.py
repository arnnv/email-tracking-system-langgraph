"""
Core job tracking functionality for the Email Tracking System
"""

import os
import pandas as pd
from datetime import datetime

# Define constants used for job tracking
JOB_COLUMNS = ["id", "sender_name", "sender_email", "company_name", "job_title", "application_status", "user_applied"]
VALID_APPLICATION_STATUSES = {"pending", "interview scheduled", "accepted", "rejected"}

def get_status_priority(status):
    """
    Get the priority level of a job application status.
    
    Args:
        status: The application status string
        
    Returns:
        Integer priority level (higher = more important)
    """
    status_priority = {
        "pending": 0,
        "interview scheduled": 1,
        "accepted": 2,
        "rejected": 3
    }
    return status_priority.get(status.lower(), -1)

def should_update_status(current_status, new_status):
    """
    Determine if the application status should be updated based on priority.
    
    Args:
        current_status: Current application status
        new_status: New application status
        
    Returns:
        Boolean indicating if the status should be updated
    """
    current_priority = get_status_priority(current_status)
    new_priority = get_status_priority(new_status)
    return new_priority > current_priority

def load_jobs_dataframe():
    """
    Load the jobs dataframe from jobs.xlsx or create a new one if it doesn't exist.
    
    Returns:
        DataFrame containing job applications
    """
    if os.path.exists("jobs.xlsx"):
        print("📂 Loading existing jobs.xlsx file", flush=True)
        jobs_df = pd.read_excel("jobs.xlsx", engine="openpyxl")
        
        # Print job application stats
        user_applied_count = jobs_df["user_applied"].sum()
        print(f"📊 Current job tracker: {len(jobs_df)} total jobs, {user_applied_count} applications", flush=True)
    else:
        print("📂 Creating new jobs dataframe", flush=True)
        jobs_df = pd.DataFrame(columns=JOB_COLUMNS)
    
    return jobs_df

def save_jobs_dataframe(jobs_df):
    """
    Save the jobs dataframe to jobs.xlsx.
    
    Args:
        jobs_df: DataFrame containing job applications
    """
    jobs_df.to_excel("jobs.xlsx", index=False, engine="openpyxl")
    
    # Print updated stats
    user_applied_count = jobs_df["user_applied"].sum()
    print(f"📊 Updated job tracker: {len(jobs_df)} total jobs, {user_applied_count} applications", flush=True)
    print("📁 Updated jobs.xlsx", flush=True)

def update_job_entry(jobs_df, company_name, job_title, application_status, 
                     email_id=None, sender_name=None, sender_email=None, user_applied=False):
    """
    Update or create a job entry in the jobs dataframe.
    
    Args:
        jobs_df: DataFrame containing job applications
        company_name: Company name
        job_title: Job title
        application_status: Application status
        email_id: Optional email ID
        sender_name: Optional sender name
        sender_email: Optional sender email
        user_applied: Whether the user has applied for the job
        
    Returns:
        Updated DataFrame and whether a new entry was created
    """
    # Find existing entry
    existing_entry = jobs_df[
        (jobs_df["company_name"].str.lower() == company_name.lower()) & 
        (jobs_df["job_title"].str.lower() == job_title.lower())
    ]
    
    new_entry_created = False
    
    if not existing_entry.empty:
        print(f"🔍 Found existing entry for {company_name} - {job_title}", flush=True)
        
        # Get current values
        current_user_applied = existing_entry["user_applied"].iloc[0]
        current_status = existing_entry["application_status"].iloc[0]
        
        # Preserve user_applied if True
        if user_applied:
            jobs_df.loc[existing_entry.index, "user_applied"] = True
            print(f"✅ Marked job as applied by user: {company_name} - {job_title}", flush=True)
        
        # Only update application status if appropriate
        if user_applied and current_user_applied:
            # If both are user applied, only update if new status is more significant
            if should_update_status(current_status, application_status):
                jobs_df.loc[existing_entry.index, "application_status"] = application_status
                print(f"✅ Updated application status to: {application_status}", flush=True)
            else:
                print(f"ℹ️ Preserving existing application status: {current_status}", flush=True)
        elif current_user_applied:
            # If it's already marked as user applied, be careful about overwriting the status
            if should_update_status(current_status, application_status):
                jobs_df.loc[existing_entry.index, "application_status"] = application_status
                print(f"✅ Updated application status to: {application_status}", flush=True)
            else:
                print("ℹ️ Keeping existing application status due to user applied flag", flush=True)
        else:
            # Normal update for non-user-applied jobs
            jobs_df.loc[existing_entry.index, "application_status"] = application_status
            print(f"✅ Updated job application: {company_name} - {job_title} ({application_status})", flush=True)
        
        # Update source info if provided
        if email_id:
            jobs_df.loc[existing_entry.index, "id"] = email_id
        if sender_name:
            jobs_df.loc[existing_entry.index, "sender_name"] = sender_name
        if sender_email:
            jobs_df.loc[existing_entry.index, "sender_email"] = sender_email
    else:
        print(f"🔍 No existing entry found for {company_name} - {job_title}", flush=True)
        
        # Generate an ID if not provided
        if not email_id:
            email_id = f"user-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create new entry
        new_entry = {
            "id": email_id,
            "sender_name": sender_name or "Unknown",
            "sender_email": sender_email or "unknown@example.com",
            "company_name": company_name,
            "job_title": job_title,
            "application_status": application_status,
            "user_applied": user_applied
        }
        
        jobs_df = pd.concat([jobs_df, pd.DataFrame([new_entry])], ignore_index=True)
        print(f"➕ Added new job application: {company_name} - {job_title} ({application_status})", flush=True)
        new_entry_created = True
    
    return jobs_df, new_entry_created 