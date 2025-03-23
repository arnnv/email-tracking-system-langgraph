#!/usr/bin/env python3
"""
Command-line tool for viewing job applications in the Email Tracking System
"""

import sys
import argparse
from jobs.viewer import load_job_applications, format_job_applications, get_application_statistics

def main():
    parser = argparse.ArgumentParser(description="View job applications in the Email Tracking System")
    parser.add_argument("--applied", action="store_true", help="Only show jobs you've applied for")
    parser.add_argument("--status", type=str, choices=["pending", "interview scheduled", "accepted", "rejected"], 
                        help="Filter by application status")
    parser.add_argument("--detailed", action="store_true", help="Show detailed information")
    
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print("📋 JOB APPLICATIONS TRACKER")
    print("="*50)
    
    if args.applied:
        print("📌 Showing only jobs you've applied for")
    if args.status:
        print(f"📌 Filtering by status: {args.status}")
    
    jobs_df = load_job_applications(applied_only=args.applied, status_filter=args.status)
    formatted_output = format_job_applications(jobs_df, detailed=args.detailed)
    
    print("\n" + formatted_output + "\n")
    
    if jobs_df is not None and not jobs_df.empty:
        # Get and print statistics
        stats = get_application_statistics(jobs_df)
        
        print("\n📊 SUMMARY:")
        print(f"Total jobs: {stats.get('total', 0)}")
        print(f"Applied: {stats.get('applied', 0)}")
        
        # Print status counts with title case
        for status, count in stats.items():
            if status not in ['total', 'applied']:
                print(f"{status.title()}: {count}")
    
    print("\n" + "="*50)
    return 0

if __name__ == "__main__":
    sys.exit(main()) 