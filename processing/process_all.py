from concurrent.futures import ThreadPoolExecutor, as_completed
from models.email import State
from processing.process_spam import process_spam_emails
from processing.process_jobs import process_job_emails
from processing.process_urgent import process_urgent_emails
from processing.process_general import process_general_emails

def process_all_categories(state: State) -> State:
    """
    Process emails concurrently for all four categories.
    Returns an updated state with processed email IDs removed from the emails list and combined errors.
    
    Args:
        state: Current application state
        
    Returns:
        Updated application state after processing all emails
    """
    print("\n🔄 STAGE 4: Processing emails by category...")
    print("  • Running concurrent processing for all categories")
    
    futures_results = []
    errors_all = state.get("errors", [])
    processed_ids_all = []
    debug_mode = state.get("debug_mode", False)
    
    if debug_mode:
        print("🔍 Debug mode enabled for processing stage", flush=True)
        print(f"🔍 Categories to process: {[cat for cat, emails in state['classified_emails'].items() if emails]}", flush=True)

    # First set the state to 'process' so the UI updates before we start processing
    state["processing_stage"] = "process"

    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_category = {
                executor.submit(process_spam_emails, state): "spam",
                executor.submit(process_job_emails, state): "job",
                executor.submit(process_urgent_emails, state): "urgent",
                executor.submit(process_general_emails, state): "general",
            }
            
            for future in as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    result = future.result()
                    processed_count = len(result["processed_ids"])
                    error_count = len(result["errors"])
                    
                    processed_ids_all.extend(result["processed_ids"])
                    errors_all.extend(result["errors"])
                    
                    status = "✅" if error_count == 0 else "⚠️"
                    print(f"  {status} {category.capitalize()}: processed {processed_count} emails" + 
                          (f" with {error_count} errors" if error_count > 0 else ""))
                    
                    if debug_mode and error_count > 0:
                        print(f"  🔍 Errors in {category} processor:", flush=True)
                        for err in result["errors"]:
                            print(f"      - {err}", flush=True)
                except Exception as processor_error:
                    error_msg = f"Error in {category} processor: {str(processor_error)}"
                    print(f"  ❌ {category.capitalize()} processor failed: {error_msg}")
                    
                    if debug_mode:
                        import traceback
                        trace = traceback.format_exc()
                        print(f"  🔍 Detailed traceback for {category} processor:", flush=True)
                        print(trace, flush=True)
                    else:
                        import traceback
                        print(f"  ❌ Traceback: {traceback.format_exc()}")
                        
                    errors_all.append(error_msg)
    except Exception as e:
        error_msg = f"Error in concurrent processing: {str(e)}"
        print(f"❌ {error_msg}")
        
        if debug_mode:
            import traceback
            trace = traceback.format_exc()
            print("🔍 Detailed traceback for concurrent processing:", flush=True)
            print(trace, flush=True)
        else:
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            
        errors_all.append(error_msg)

    remaining_emails = [email for email in state["emails"] if email["id"] not in processed_ids_all]
    
    print(f"\n✅ Completed processing {len(processed_ids_all)} emails")
    if remaining_emails:
        print(f"⚠️ {len(remaining_emails)} emails remain unprocessed")
        
    # Preserve all state properties
    final_state = state.copy()
    final_state.update({
        "emails": remaining_emails,
        "errors": errors_all,
        "processing_stage": "end"
    })
    
    return final_state
