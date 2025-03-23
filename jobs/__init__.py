"""
Jobs package for the Email Tracking System
"""

from jobs.applications import handle_user_job_application
from jobs.processor import process_job_emails
from jobs.viewer import load_job_applications, format_job_applications, get_application_statistics 