#!/usr/bin/env python3
"""
Command-line tool for submitting job applications to the Email Tracking System
"""

import argparse
import sys
from jobs.applications import handle_user_job_application

def main():
    parser = argparse.ArgumentParser(description="Submit a job application to the Email Tracking System")
    parser.add_argument("--email", type=str, default="", help="Your email address (optional)")
    parser.add_argument("--file", type=str, help="Path to text file containing job description (optional)")
    
    args = parser.parse_args()
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                job_description = f.read()
            print(f"📄 Reading job description from file: {args.file}")
        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
            return 1
    else:
        # If no file provided, accept input from stdin
        print("📝 Enter the job description below. Press Ctrl+D (Unix) or Ctrl+Z+Enter (Windows) when finished:")
        job_description = sys.stdin.read()
    
    if not job_description or len(job_description.strip()) < 10:
        print("❌ Job description is too short. Please provide more information.")
        return 1
    
    # Use a default placeholder if email is not provided
    user_email = args.email if args.email else "user-applied@example.com"
    
    result = handle_user_job_application(job_description, user_email)
    
    if result["success"]:
        print("\n✅ Successfully recorded application:")
        print(f"   Company: {result['company']}")
        print(f"   Position: {result['job_title']}")
        print(f"   Status: {result['status']}")
        return 0
    else:
        print(f"\n❌ Failed to process application: {result['message']}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 