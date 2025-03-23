#!/usr/bin/env python3
from dotenv import load_dotenv
from core.utils import print_db
from workflows.graph_builder import build_email_processing_graph
import config

# Load environment variables
load_dotenv()

def main():
    """
    Main entry point for the email processing application
    """
    print("\n" + "="*50)
    print("🔄 EMAIL TRACKING SYSTEM")
    print("="*50)
    print(f"📥 Email download limit: {config.EMAILS_TO_DOWNLOAD}")
    
    # Initialize language model
    llm = config.create_llm()
    print(f"🧠 Using language model: {config.LLM_MODEL}")

    # Print database state before processing
    print("\n📊 DATABASE BEFORE PROCESSING:")
    print(print_db())

    # Create initial state with explicit num_emails_to_download
    initial_state = {
        "emails": [], 
        "classified_emails": {"spam": [], "job": [], "urgent": [], "general": []}, 
        "errors": [],
        "processing_stage": "fetch",
        "num_emails_to_download": config.EMAILS_TO_DOWNLOAD,
        "model": llm,
        "debug_mode": config.DEFAULT_DEBUG_MODE
    }

    # Build and run the processing graph
    print("\n🔄 Starting email processing workflow...")
    graph, _ = build_email_processing_graph(model=llm, number_emails=config.EMAILS_TO_DOWNLOAD, debug_mode=config.DEFAULT_DEBUG_MODE)
    
    # Run the graph
    results = graph.invoke(initial_state)

    # Calculate processing statistics
    processed_total = (
        len(results['classified_emails']['spam']) + 
        len(results['classified_emails']['job']) + 
        len(results['classified_emails']['urgent']) + 
        len(results['classified_emails']['general'])
    )

    # Print results
    print("\n📊 PROCESSING SUMMARY:")
    print(f"Total emails processed: {processed_total}")
    print(f"📧 Spam: {len(results['classified_emails']['spam'])}")
    print(f"📧 Job: {len(results['classified_emails']['job'])}")
    print(f"📧 Urgent: {len(results['classified_emails']['urgent'])}")
    print(f"📧 General: {len(results['classified_emails']['general'])}")
    print(f"📧 Remaining unprocessed: {len(results['emails'])}")

    if results['errors']:
        print("\n⚠️ ERRORS ENCOUNTERED:")
        for error in results['errors']:
            print(f"  - {error}")

    print("\n📊 DATABASE AFTER PROCESSING:")
    print(print_db())
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
