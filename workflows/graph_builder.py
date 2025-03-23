from langgraph.graph import END, StateGraph
from models.email import State
from processing.fetch_emails import fetch_unprocessed_emails
from agents.summarization_agent import summarize_emails
from agents.classification_agent import classify_emails
from processing.process_all import process_all_categories

def build_email_processing_graph(model=None, number_emails=5, monitor_func=None, debug_mode=False):
    """
    Build and compile the email processing workflow graph
    
    Args:
        model: The language model to use for processing emails
        number_emails: Number of emails to download and process
        monitor_func: Function to monitor workflow progress
        debug_mode: Whether to enable debug mode for detailed logging
        
    Returns:
        Compiled state graph
    """
    print(f"🔄 Building email processing workflow graph with debug_mode={debug_mode}...")
    
    # Create initial state
    initial_state = {
        "emails": [], 
        "classified_emails": {"spam": [], "job": [], "urgent": [], "general": []}, 
        "errors": [],
        "processing_stage": "fetch",
        "num_emails_to_download": number_emails,
        "model": model,
        "debug_mode": debug_mode
    }
    
    # Initialize callbacks list
    callbacks = []
    if monitor_func:
        callbacks.append(monitor_func)

    # Callback wrapper to update the state
    def add_callback_to_stage(func):
        def wrapper(state):
            # Call the original function to get the next state
            if debug_mode:
                print(f"🔍 Running stage: {func.__name__}", flush=True)
                
            try:
                next_state = func(state)
                
                if debug_mode:
                    print(f"✅ Completed stage: {func.__name__}", flush=True)
            except Exception as e:
                if debug_mode:
                    print(f"❌ Error in stage {func.__name__}: {str(e)}", flush=True)
                    import traceback
                    print(traceback.format_exc(), flush=True)
                
                # Add the error to the state and continue
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(f"Error in {func.__name__}: {str(e)}")
                
                # If we're in fetch stage and fail, we should end the workflow
                if func.__name__ == "fetch_unprocessed_emails":
                    state["processing_stage"] = "end"
                
                next_state = state
            
            # Call all callbacks with the new state
            for callback in callbacks:
                try:
                    callback_result = callback(next_state)
                    if callback_result:
                        next_state = callback_result
                except Exception as callback_error:
                    if debug_mode:
                        print(f"❌ Error in callback: {str(callback_error)}", flush=True)
                    
                    if "errors" not in next_state:
                        next_state["errors"] = []
                    next_state["errors"].append(f"Callback error: {str(callback_error)}")
                
            return next_state
        return wrapper

    # Create the graph
    graph = StateGraph(State)

    # Wrap all stage functions with callbacks
    fetch_with_callbacks = add_callback_to_stage(fetch_unprocessed_emails)
    summarize_with_callbacks = add_callback_to_stage(summarize_emails)
    classify_with_callbacks = add_callback_to_stage(classify_emails)
    process_with_callbacks = add_callback_to_stage(process_all_categories)

    # Add nodes with callback-wrapped functions
    graph.add_node("fetch", fetch_with_callbacks)
    graph.add_node("summarize", summarize_with_callbacks)  
    graph.add_node("classify", classify_with_callbacks)
    graph.add_node("process_parallel", process_with_callbacks)

    # Router function to determine next step
    def router(state: State) -> str:
        """
        Route to the next step based on processing_stage in state.
        """
        # Get the current processing stage, default to "fetch" if not set
        current_stage = state.get("processing_stage", "fetch")
        
        if debug_mode:
            print(f"🔍 Router: current stage is '{current_stage}'", flush=True)
        
        # Always return the current processing stage as set in the state
        # The stage transitions are handled in each processing function
        return current_stage

    # Add conditional edges - use simpler approach
    # We need to include all possible destinations from the router function
    edges = {
        "fetch": "fetch",
        "summarize": "summarize",
        "classify": "classify",
        "process": "process_parallel",
        "process_parallel": "process_parallel",
        "end": END
    }
    
    graph.add_conditional_edges(
        "fetch",
        router,
        edges
    )

    graph.add_conditional_edges(
        "summarize",
        router,
        edges
    )

    graph.add_conditional_edges(
        "classify",
        router,
        edges
    )

    graph.add_conditional_edges(
        "process_parallel",
        router,
        edges
    )

    # Set entry point
    graph.set_entry_point("fetch")
    
    # Compile the graph
    compiled_graph = graph.compile()
    print("✅ Email processing workflow graph compiled")
    return compiled_graph, initial_state
