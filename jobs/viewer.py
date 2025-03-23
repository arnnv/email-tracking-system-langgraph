"""
Module for viewing job applications in the Email Tracking System
"""

import os
from tabulate import tabulate
from jobs.tracker import load_jobs_dataframe

def load_job_applications(applied_only=False, status_filter=None):
    """
    Load job applications from jobs.xlsx with optional filtering
    
    Args:
        applied_only: Only show jobs the user has applied for
        status_filter: Filter by application status
        
    Returns:
        DataFrame of job applications
    """
    if not os.path.exists("jobs.xlsx"):
        print("❌ No jobs.xlsx file found. No job applications to display.")
        return None
    
    try:
        jobs_df = load_jobs_dataframe()
        
        if jobs_df.empty:
            print("❌ No job applications found in jobs.xlsx.")
            return None
            
        # Apply filters
        if applied_only:
            jobs_df = jobs_df[jobs_df["user_applied"] == True]
            
        if status_filter and status_filter.lower() in ["pending", "interview scheduled", "accepted", "rejected"]:
            jobs_df = jobs_df[jobs_df["application_status"].str.lower() == status_filter.lower()]
            
        return jobs_df
        
    except Exception as e:
        print(f"❌ Error loading job applications: {str(e)}")
        return None

def format_job_applications(jobs_df, detailed=False):
    """
    Format job applications for display
    
    Args:
        jobs_df: DataFrame of job applications
        detailed: Whether to show detailed information
        
    Returns:
        Formatted string of job applications
    """
    if jobs_df is None or jobs_df.empty:
        return "No job applications found matching the criteria."
    
    # Choose columns based on detail level
    if detailed:
        display_cols = ["company_name", "job_title", "application_status", "user_applied", 
                       "sender_name", "sender_email", "id"]
    else:
        display_cols = ["company_name", "job_title", "application_status", "user_applied"]
    
    # Only include columns that exist
    display_cols = [col for col in display_cols if col in jobs_df.columns]
    
    # Format the output
    formatted_df = jobs_df[display_cols].copy()
    
    # Rename columns for better display
    formatted_df.columns = [col.replace('_', ' ').title() for col in display_cols]
    
    # Convert boolean to yes/no
    if "User Applied" in formatted_df.columns:
        formatted_df["User Applied"] = formatted_df["User Applied"].map({True: "✅ Yes", False: "❌ No"})
    
    # Format application status with emojis
    if "Application Status" in formatted_df.columns:
        formatted_df["Application Status"] = formatted_df["Application Status"].map({
            "pending": "⏳ Pending",
            "interview scheduled": "🗓️ Interview",
            "accepted": "🎉 Accepted",
            "rejected": "❌ Rejected"
        })
    
    return tabulate(formatted_df, headers="keys", tablefmt="grid", showindex=False)

def get_application_statistics(jobs_df):
    """
    Generate statistics about job applications
    
    Args:
        jobs_df: DataFrame of job applications
        
    Returns:
        Dictionary of statistics
    """
    if jobs_df is None or jobs_df.empty:
        return {}
    
    stats = {
        "total": len(jobs_df),
        "applied": jobs_df["user_applied"].sum() if "user_applied" in jobs_df.columns else 0
    }
    
    if "application_status" in jobs_df.columns:
        status_counts = jobs_df["application_status"].value_counts().to_dict()
        stats.update(status_counts)
    
    return stats 