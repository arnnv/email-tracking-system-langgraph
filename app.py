#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import os
import time
from dotenv import load_dotenv
from core.initialize_db import initialize_db, connect_to_db
from workflows.graph_builder import build_email_processing_graph
from jobs.applications import handle_user_job_application
from jobs.viewer import load_job_applications, get_application_statistics
from jobs.tracker import load_jobs_dataframe, save_jobs_dataframe
import config

# Load environment variables
load_dotenv()

# ===== CONFIGURATION =====
EMAILS_TO_DOWNLOAD = config.EMAILS_TO_DOWNLOAD
EMAILS_PER_PAGE = config.EMAILS_PER_PAGE
DEFAULT_DEBUG_MODE = config.DEFAULT_DEBUG_MODE
# =========================

# Page configuration
st.set_page_config(
    page_title="Email & Job Tracking System",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom font loader
def load_custom_font():
    font_loader = """
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {
            font-family: 'Roboto', sans-serif !important;
        }
    </style>
    """
    st.markdown(font_loader, unsafe_allow_html=True)

# Call the font loader before any other content
load_custom_font()

# Database initialization function
def initialize_database():
    """Initialize the emails database if it doesn't exist"""
    try:
        # Use the existing function from core.initialize_db
        initialize_db()
        if not os.path.exists(config.DB_PATH):
            st.error("Failed to create database file")
            return False
        else:
            if not os.path.exists(config.DB_PATH) or os.path.getsize(config.DB_PATH) == 0:
                st.success("Database initialized successfully.")
            return True
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        return False

def initialize_jobs_database():
    """Initialize the jobs tracking Excel file if it doesn't exist"""
    try:
        # Check if the jobs Excel file exists
        if not os.path.exists('jobs.xlsx'):
            st.info("Jobs tracking file not found. Creating a new jobs database...")
            
            # Use the load_jobs_dataframe function which handles initialization
            # if the file doesn't exist
            jobs_df = load_jobs_dataframe()
            
            # Save the jobs dataframe
            save_jobs_dataframe(jobs_df)
            
            st.success("Jobs tracking database initialized successfully.")
            return True
        
        return True
    except Exception as e:
        st.error(f"Error initializing jobs database: {str(e)}")
        return False

# Apply custom CSS
def load_css():
    if os.path.exists('.streamlit/style.css'):
        with open('.streamlit/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize databases on app startup
initialize_database()
initialize_jobs_database()

# Load custom CSS
load_css()

# App title and description
st.title("📧 Email & Job Tracking System")
st.markdown("Track your emails and job applications in one place")

# Add a subtle separator
st.markdown('<hr style="height:1px;border:none;background-color:#333;" />', unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")

# Check if nav parameter is in query params
query_params = st.query_params
default_page = "Emails"
if "nav" in query_params:
    nav_param = query_params["nav"]
    if nav_param in ["Emails", "Jobs", "Apply for Job"]:
        default_page = nav_param

page = st.sidebar.radio("Go to", ["Emails", "Jobs", "Apply for Job"], index=["Emails", "Jobs", "Apply for Job"].index(default_page))

# Add app info in sidebar
with st.sidebar.expander("About", expanded=False):
    st.markdown("""
    **Email & Job Tracking System** helps you:
    - Download and categorize emails
    - Track job applications
    - Apply for jobs
    
    Built with Streamlit and Langchain.
    """)

# Helper functions
def check_database_structure():
    """Check if the database has the required structure"""
    try:
        # Check if the file exists
        if not os.path.exists(config.DB_PATH):
            # If the file doesn't exist, initialize a new database
            from core.initialize_db import initialize_db
            initialize_db()
            return True, "Database initialized successfully."
        
        # Check if the file is a valid database file
        if not os.path.getsize(config.DB_PATH) > 0:
            return False, "Database file exists but appears to be empty or corrupt."
        
        # Connect to the database
        conn = connect_to_db()
        cursor = conn.cursor()
        
        # Check if emails table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
        if not cursor.fetchone():
            conn.close()
            return False, "Database file exists but 'emails' table is missing."
        
        # Check if the table has the required columns
        required_columns = ['id', 'date', 'sender', 'email', 'subject', 'body', 'summary', 'email_processed', 'category']
        cursor.execute("PRAGMA table_info(emails)")
        existing_columns = [info[1] for info in cursor.fetchall()]
        
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            # Check if the table has data
            cursor.execute("SELECT COUNT(*) FROM emails")
            has_data = cursor.fetchone()[0] > 0
            conn.close()
            
            if has_data:
                return False, f"Table has data so it cannot be automatically fixed. Missing columns: {', '.join(missing_columns)}"
            else:
                # If the table exists but has no data, we can drop and recreate it
                from core.initialize_db import initialize_db
                cursor.execute("DROP TABLE emails")
                conn.commit()
                conn.close()
                initialize_db()
                return True, "Empty database rebuilt with correct schema."
        
        conn.close()
        return True, "Database structure is valid."
        
    except Exception as e:
        return False, f"Error checking database: {str(e)}"

def load_emails_from_db():
    """Load emails from the SQLite database"""
    try:
        # First make sure database is initialized
        if not os.path.exists(config.DB_PATH):
            initialize_database()
            # Return empty DataFrame if we just created the database
            return pd.DataFrame()
        
        # Connect to the database
        conn = connect_to_db()
        cursor = conn.cursor()
        
        # Check if emails table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
        if not cursor.fetchone():
            # Table doesn't exist
            conn.close()
            return pd.DataFrame()
        
        # Table exists, proceed with query
        query = """
        SELECT id, email, sender, subject, summary, email_processed, 
               category, date 
        FROM emails 
        ORDER BY date DESC
        """
        emails_df = pd.read_sql_query(query, conn)
        conn.close()
        return emails_df
    except Exception as e:
        st.error(f"Error loading emails: {str(e)}")
        return pd.DataFrame()

def render_workflow_stage(title, description, icon, status="pending", details=None):
    """Render a workflow stage with appropriate styling based on status"""
    status_class = ""
    if status == "active":
        status_class = "active"
    elif status == "completed":
        status_class = "completed"
        
    st.markdown(f"""
    <div class="workflow-stage {status_class}">
        <div style="display: flex; align-items: center;">
            <span class="workflow-icon">{icon}</span>
            <strong>{title}</strong>
            <span style="margin-left: auto;">
                {get_status_icon(status)}
            </span>
        </div>
        <div style="margin-top: 5px; font-size: 0.9em; color: #AAA;">
            {description}
        </div>
        {f'<div style="margin-top: 8px; font-size: 0.85em;">{details}</div>' if details else ''}
    </div>
    """, unsafe_allow_html=True)

def get_status_icon(status):
    """Get an appropriate icon for the workflow stage status"""
    if status == "completed":
        return '<span style="color: #00cc66;">✓</span>'
    elif status == "active":
        return '<span style="color: #4F8BF9;">⟳</span>'
    elif status == "error":
        return '<span style="color: #ff5f5f;">✗</span>'
    else:
        return '<span style="color: #888;">○</span>'

def process_emails_with_workflow(num_emails=EMAILS_TO_DOWNLOAD, debug_mode=False):
    """Process emails using the email processing graph with detailed workflow stages"""
    # Define the workflow stages
    workflow_stages = {
        "initialize": {
            "title": "Initialize System",
            "description": "Loading language model and setting up the environment",
            "icon": "🔄",
            "status": "pending"
        },
        "fetch": {
            "title": "Fetch Emails",
            "description": f"Downloading up to {num_emails} emails from server",
            "icon": "📥",
            "status": "pending"
        },
        "summarize": {
            "title": "Summarize Emails",
            "description": "Creating concise summaries of email content",
            "icon": "📝",
            "status": "pending"
        },
        "classify": {
            "title": "Classify Emails",
            "description": "Categorizing emails into spam, job, urgent, and general",
            "icon": "🏷️",
            "status": "pending"
        },
        "process_spam": {
            "title": "Process Spam",
            "description": "Handling spam emails",
            "icon": "🚫",
            "status": "pending"
        },
        "process_job": {
            "title": "Process Job Applications",
            "description": "Extracting and storing job application details",
            "icon": "💼",
            "status": "pending"
        },
        "process_urgent": {
            "title": "Process Urgent Emails",
            "description": "Handling time-sensitive emails",
            "icon": "🔥",
            "status": "pending"
        },
        "process_general": {
            "title": "Process General Emails",
            "description": "Processing remaining emails",
            "icon": "📋",
            "status": "pending"
        },
        "complete": {
            "title": "Complete",
            "description": "Email processing workflow completed",
            "icon": "✅",
            "status": "pending"
        }
    }
    
    # Create columns for progress display
    col1, col2 = st.columns([1, 2])
    
    # Create placeholders for dynamic content
    status_container = col1.empty()
    details_container = col2.empty()
    error_container = st.empty()
    results_container = st.empty()
    
    # Create a debug container if debug mode is on
    debug_container = st.empty() if debug_mode else None
    
    # Update a single workflow stage and render it
    def update_stage(stage_name, status, details=None):
        workflow_stages[stage_name]["status"] = status
        if details:
            workflow_stages[stage_name]["details"] = details
        render_workflow_state(status_container, workflow_stages)
        
        # Update the details container based on status
        if status == "active":
            details_container.info(workflow_stages[stage_name]["description"])
        elif status == "completed":
            details_container.success(details if details else f"Completed: {workflow_stages[stage_name]['title']}")
        elif status == "error":
            details_container.error(details if details else f"Error in {workflow_stages[stage_name]['title']}")

    # Monitor and respond to stage changes in the workflow
    def workflow_monitor(state):
        """Monitor the workflow state changes and update the UI"""
        current_stage = state.get("processing_stage", "fetch")
        
        # Debug logging
        if debug_mode:
            print(f"🔍 Workflow Monitor - Stage: {current_stage}", flush=True)
            
            # Show state info in debug container
            try:
                # Create a simplified version of the state for display
                display_state = {
                    "processing_stage": state.get("processing_stage", "unknown"),
                    "emails_count": len(state.get("emails", [])),
                    "classified_emails": {k: len(v) for k, v in state.get("classified_emails", {}).items()},
                    "errors_count": len(state.get("errors", [])),
                }
                
                # Show errors in detail if there are any
                if state.get("errors", []):
                    display_state["errors"] = state.get("errors", [])
                
                debug_container.code(f"Current State: {display_state}")
            except Exception as debug_error:
                print(f"🔍 Debug display error: {str(debug_error)}", flush=True)
                pass
        
        # Determine which stage is active based on the workflow state
        if current_stage == "fetch":
            update_stage("fetch", "active")
        elif current_stage == "summarize":
            # Fetch stage is completed when we move to summarize
            update_stage("fetch", "completed", f"Downloaded emails. Total emails to process: {len(state.get('emails', []))}")
            update_stage("summarize", "active")
        elif current_stage == "classify":
            # Summarize stage is completed when we move to summarize
            update_stage("summarize", "completed", f"Summarized {len(state.get('emails', []))} emails")
            update_stage("classify", "active")
        elif current_stage == "process" or current_stage == "process_parallel":
            # Classification is complete, show the counts
            try:
                spam_count = len(state['classified_emails']['spam'])
                job_count = len(state['classified_emails']['job'])
                urgent_count = len(state['classified_emails']['urgent'])
                general_count = len(state['classified_emails']['general'])
                
                # First mark classification as completed if it's not already
                if workflow_stages["classify"]["status"] != "completed":
                    update_stage("classify", "completed", 
                                f"Classified emails: {spam_count} spam, {job_count} job, {urgent_count} urgent, {general_count} general")
                
                # Process stages - set all to active that have items
                if spam_count > 0 and workflow_stages["process_spam"]["status"] != "completed":
                    update_stage("process_spam", "active", f"Processing {spam_count} spam emails...")
                if job_count > 0 and workflow_stages["process_job"]["status"] != "completed":
                    update_stage("process_job", "active", f"Processing {job_count} job emails...")
                if urgent_count > 0 and workflow_stages["process_urgent"]["status"] != "completed":
                    update_stage("process_urgent", "active", f"Processing {urgent_count} urgent emails...")
                if general_count > 0 and workflow_stages["process_general"]["status"] != "completed":
                    update_stage("process_general", "active", f"Processing {general_count} general emails...")
            except Exception as e:
                error_msg = f"Error updating UI during processing stage: {str(e)}"
                if debug_mode:
                    error_container.error(error_msg)
                    import traceback
                    error_container.code(traceback.format_exc())
                print(f"❌ {error_msg}", flush=True)
        elif current_stage == "end":
            # Mark all processing stages as completed
            try:
                spam_count = len(state['classified_emails']['spam'])
                job_count = len(state['classified_emails']['job'])
                urgent_count = len(state['classified_emails']['urgent'])
                general_count = len(state['classified_emails']['general'])
                
                if spam_count > 0:
                    update_stage("process_spam", "completed", f"Processed {spam_count} spam emails")
                if job_count > 0:
                    update_stage("process_job", "completed", f"Processed {job_count} job emails")
                if urgent_count > 0:
                    update_stage("process_urgent", "completed", f"Processed {urgent_count} urgent emails")
                if general_count > 0:
                    update_stage("process_general", "completed", f"Processed {general_count} general emails")
                
                # Mark workflow as complete
                update_stage("complete", "active")
                
                # Final update
                processed_total = spam_count + job_count + urgent_count + general_count
                details_text = f"Email processing complete! {processed_total} emails processed in total."
                update_stage("complete", "completed", details_text)
                
                # Show errors if any
                if state.get("errors", []):
                    error_container.error(f"Completed with {len(state['errors'])} errors:")
                    for error in state["errors"]:
                        error_container.error(error)
            except Exception as e:
                error_msg = f"Error updating UI during end stage: {str(e)}"
                if debug_mode:
                    error_container.error(error_msg)
                    import traceback
                    error_container.code(traceback.format_exc())
                print(f"❌ {error_msg}", flush=True)
        
        return state
    
    try:
        print(f"🚀 Starting email processing for {num_emails} emails with debug_mode={debug_mode}", flush=True)
        
        # Mark initialize stage as active
        update_stage("initialize", "active")
        
        # Check if we can connect to the database and get email count
        try:
            conn = connect_to_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM emails")
            current_email_count = cursor.fetchone()[0]
            conn.close()
            
            update_stage("initialize", "completed", f"Database initialized. Current emails in database: {current_email_count}")
        except Exception as db_error:
            error_msg = f"Database error: {str(db_error)}"
            print(f"❌ {error_msg}", flush=True)
            if debug_mode:
                import traceback
                error_container.code(traceback.format_exc())
            raise Exception(error_msg)
        
        # Initialize the language model
        try:
            model = config.create_llm()
            update_stage("initialize", "completed", f"Language model initialized: {config.LLM_MODEL}")
        except Exception as model_error:
            error_msg = f"Model initialization error: {str(model_error)}"
            print(f"❌ {error_msg}", flush=True)
            update_stage("initialize", "error", error_msg)
            if debug_mode:
                import traceback
                error_container.code(traceback.format_exc())
            raise Exception(f"Failed to initialize language model: {str(model_error)}")
        
        # Build the graph
        try:
            graph, initial_state = build_email_processing_graph(model=model, number_emails=num_emails, monitor_func=workflow_monitor, debug_mode=debug_mode)
        except Exception as graph_error:
            error_msg = f"Error building workflow graph: {str(graph_error)}"
            print(f"❌ {error_msg}", flush=True)
            if debug_mode:
                import traceback
                error_container.code(traceback.format_exc())
            raise Exception(error_msg)
        
        # Invoke the graph with initial state
        try:
            results = graph.invoke(initial_state)
            print("✅ Email processing completed successfully", flush=True)
        except Exception as workflow_error:
            error_msg = f"Error in workflow execution: {str(workflow_error)}"
            print(f"❌ {error_msg}", flush=True)
            if debug_mode:
                import traceback
                error_container.code(traceback.format_exc())
            raise Exception(error_msg)
        
        # Get the counts for each category
        spam_count = len(results["classified_emails"]["spam"])
        job_count = len(results["classified_emails"]["job"])
        urgent_count = len(results["classified_emails"]["urgent"])
        general_count = len(results["classified_emails"]["general"])
        processed_total = spam_count + job_count + urgent_count + general_count
        
        # Ensure all stages are completed in the UI
        workflow_monitor({"processing_stage": "end", "classified_emails": results["classified_emails"], "errors": results.get("errors", [])})
        
        # Display final results
        results_container.success("Email Processing Completed Successfully!")
        
        # Display statistics in metrics
        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric("Spam", spam_count)
        with metric_cols[1]:
            st.metric("Job", job_count)
        with metric_cols[2]:
            st.metric("Urgent", urgent_count)
        with metric_cols[3]:
            st.metric("General", general_count)
            
        if results.get('errors', []):
            error_container.error(f"Completed with {len(results['errors'])} errors:")
            for error in results['errors']:
                error_container.error(error)
                
        return True, "Processing completed successfully!"
    
    except Exception as e:
        # If we have a current_stage, mark it as error
        active_stages = [stage for stage, details in workflow_stages.items() 
                        if details["status"] == "active"]
        if active_stages:
            update_stage(active_stages[0], "error", str(e))
        
        error_message = f"Error processing emails: {str(e)}"
        error_container.error(error_message)
        details_container.error("An error occurred. Please check the error details below.")
        
        # Show stack trace if debug mode is enabled
        if debug_mode:
            import traceback
            stack_trace = traceback.format_exc()
            error_container.code(stack_trace)
            print(f"❌ Error stack trace:\n{stack_trace}", flush=True)
        
        return False, error_message

def render_workflow_state(container, workflow_stages):
    """Render the current state of all workflow stages"""
    stages_html = ""
    for stage_id, stage in workflow_stages.items():
        stages_html += f"""
        <div class="workflow-stage {stage['status']}">
            <div style="display: flex; align-items: center;">
                <span class="workflow-icon">{stage['icon']}</span>
                <strong>{stage['title']}</strong>
                <span style="margin-left: auto;">
                    {get_status_icon(stage['status'])}
                </span>
            </div>
            <div style="margin-top: 5px; font-size: 0.9em; color: #AAA;">
                {stage['description']}
            </div>
            {f'<div style="margin-top: 8px; font-size: 0.85em;">{stage.get("details", "")}</div>' if stage.get("details") else ''}
        </div>
        """
    
    container.markdown(stages_html, unsafe_allow_html=True)
    
def format_category(category):
    """Format category with appropriate icon"""
    icons = {
        "spam": "🚫",
        "job": "💼",
        "urgent": "🔥",
        "general": "📝",
        None: "❓"
    }
    return f"{icons.get(category, '❓')} {category.title() if category else 'Unclassified'}"

def format_processed(processed):
    """Format processed status with appropriate icon"""
    return "✅ Yes" if processed else "❌ No"

# Application pages
if page == "Emails":
    st.header("Email Management")
    
    # Debug mode toggle
    with st.sidebar:
        debug_mode = st.checkbox("Debug Mode", value=DEFAULT_DEBUG_MODE, help="Show detailed technical information for debugging")
    
    # Check database structure before proceeding
    db_valid, db_message = check_database_structure()
    if not db_valid:
        st.error(f"Database Error: {db_message}")
        
        # If the issue is with missing columns and there's data, suggest manual fix
        if "Table has data so it cannot be automatically fixed" in db_message:
            st.warning("The database structure needs to be updated, but it contains data that would be lost if updated automatically.")
            st.info("Options to fix this issue:")
            st.markdown("""
            1. **Backup and recreate**: Export your data first, then recreate the database.
            2. **Manually add columns**: Use a SQLite editor to add the missing columns.
            3. **Create new database**: Move your emails.db file and restart the app to create a fresh database.
            """)
            
            # Display what columns are missing for easier manual fixing
            if "Missing columns" in db_message:
                st.code(db_message)
        else:
            st.info("Please try restarting the app. If the issue persists, check the error message above for more details.")
    else:
        if db_message != "Database structure is valid.":
            st.success(db_message)
            
        # Email processing section
        with st.expander("Process New Emails", expanded=True):
            email_processing_cols = st.columns([3, 1])
            
            with email_processing_cols[0]:
                st.markdown("### Download and Process New Emails")
                st.markdown("Click the button below to download and process new emails.")
            
            with email_processing_cols[1]:
                num_emails = st.number_input("Emails to download", min_value=1, max_value=50, value=10)
            
            # Button to trigger email processing
            if st.button("Process Emails", use_container_width=True):
                with st.spinner("Processing emails..."):
                    success, message = process_emails_with_workflow(num_emails, debug_mode)
                    
                    # Show additional debug info if in debug mode
                    if debug_mode and not success:
                        st.error("Debug Information:")
                        st.error(message)
            
            # Show refresh data button
            if st.button("Refresh Data", use_container_width=True):
                st.rerun()
            
        # Email Display Section
        st.markdown("## Your Emails")
        emails_df = load_emails_from_db()
        
        if emails_df.empty:
            # Check if database exists but is empty vs. newly created
            db_initialized = False
            if os.path.exists(config.DB_PATH):
                conn = connect_to_db()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
                if cursor.fetchone():  # Table exists
                    cursor.execute("SELECT COUNT(*) FROM emails")
                    count = cursor.fetchone()[0]
                    if count == 0:  # Table exists but is empty
                        db_initialized = True
                conn.close()
            
            if db_initialized:
                st.info("No emails found in the database. Click 'Process Emails' to download and process emails.")
            else:
                st.success("Email database has been initialized.")
                st.info("To get started, click 'Process Emails' to download and process emails from your account.")
                
            # Show a visual guide
            st.markdown("""
            ### Getting Started
            
            1. **Configure Email Settings**: Make sure your .env file contains your email credentials
            2. **Process Emails**: Click the 'Process Emails' button above
            3. **View Results**: After processing, your emails will appear here
            """)
        else:
            # Filter controls
            filter_cols = st.columns(4)
            
            with filter_cols[0]:
                # Clean up the categories list to handle None values
                categories = emails_df["category"].fillna("uncategorized").unique().tolist()
                filter_category = st.selectbox("Filter by Category", ["All"] + sorted(categories))
            
            with filter_cols[1]:
                filter_processed = st.selectbox("Filter by Status", ["All", "Processed", "Unprocessed"])
            
            with filter_cols[2]:
                search_term = st.text_input("Search in Subject")
            
            with filter_cols[3]:
                sort_by = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Category"])
            
            # Apply filters
            filtered_df = emails_df.copy()
            if filter_category != "All":
                if filter_category == "uncategorized":
                    filtered_df = filtered_df[filtered_df["category"].isna()]
                else:
                    filtered_df = filtered_df[filtered_df["category"] == filter_category]
            
            if filter_processed != "All":
                if filter_processed == "Processed":
                    filtered_df = filtered_df[filtered_df["email_processed"] == 1]
                else:
                    filtered_df = filtered_df[filtered_df["email_processed"] == 0]
            
            if search_term:
                filtered_df = filtered_df[filtered_df["subject"].str.contains(search_term, case=False)]
            
            # Apply sorting
            if sort_by == "Date (newest)":
                filtered_df = filtered_df.sort_values("date", ascending=False)
            elif sort_by == "Date (oldest)":
                filtered_df = filtered_df.sort_values("date", ascending=True)
            elif sort_by == "Category":
                filtered_df = filtered_df.sort_values(["category", "date"], ascending=[True, False])
            
            # Show statistics
            stat_cols = st.columns(4)
            
            with stat_cols[0]:
                st.metric("Total Emails", len(emails_df))
            
            with stat_cols[1]:
                st.metric("Processed", len(emails_df[emails_df["email_processed"] == 1]))
            
            with stat_cols[2]:
                st.metric("Unprocessed", len(emails_df[emails_df["email_processed"] == 0]))
            
            with stat_cols[3]:
                # Count by category
                # Fill NA values with "uncategorized" for better display
                category_counts = emails_df["category"].fillna("uncategorized").value_counts()
                if not category_counts.empty:
                    top_category = category_counts.index[0]
                    top_count = category_counts.iloc[0]
                    # Format uncategorized for display
                    display_category = top_category if top_category != "uncategorized" else "Uncategorized"
                    st.metric("Top Category", f"{display_category} ({top_count})")
                else:
                    st.metric("Top Category", "None (0)")
            
            # Display emails with pagination
            EMAILS_PER_PAGE = 10
            total_pages = max(1, (len(filtered_df) + EMAILS_PER_PAGE - 1) // EMAILS_PER_PAGE)
            
            # Get page from query parameters if available
            query_params = st.query_params
            default_page = 1
            if "page" in query_params:
                try:
                    default_page = int(query_params["page"])
                    if default_page < 1 or default_page > total_pages:
                        default_page = 1
                except ValueError:
                    default_page = 1
            
            page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=default_page)
            
            start_idx = (page_number - 1) * EMAILS_PER_PAGE
            end_idx = min(start_idx + EMAILS_PER_PAGE, len(filtered_df))
            
            if len(filtered_df) > 0:
                st.markdown(f"**Showing {start_idx+1}-{end_idx} of {len(filtered_df)} emails**")
                
                # Email cards
                for _, email in filtered_df.iloc[start_idx:end_idx].iterrows():
                    # Determine card color based on category
                    card_bg_color = "#1E1E1E"
                    category_color = "#333333"  # Default color
                    
                    # Handle None category
                    category = email["category"] if email["category"] is not None else "uncategorized"
                    
                    if category == "spam":
                        category_color = "#FF4B4B"
                    elif category == "job":
                        category_color = "#4B83FF"
                    elif category == "urgent":
                        category_color = "#FFB347"
                    elif category == "general":
                        category_color = "#47C9FF"
                    
                    # Create card
                    st.markdown(f"""
                    <div style="background-color: {card_bg_color}; padding: 15px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid {category_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="font-size: 16px;">{email['subject']}</strong>
                                <div style="font-size: 14px; color: #AAAAAA;">From: {email['sender']}</div>
                            </div>
                            <div>
                                <span style="background-color: {category_color}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">{email['category'].upper() if email['category'] is not None else 'UNCATEGORIZED'}</span>
                                <span style="margin-left: 10px; font-size: 12px; color: #AAAAAA;">{email['date']}</span>
                            </div>
                        </div>
                        <div style="margin-top: 10px; font-size: 14px;">{email['summary']}</div>
                        <div style="margin-top: 5px; display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-size: 12px; color: {'#00CC66' if email['email_processed'] == 1 else '#FF4B4B'};">
                                {'✓ Processed' if email['email_processed'] == 1 else '⦿ Not Processed'}
                            </div>
                            <div>
                                <a href="mailto:{email['email']}?subject=Re: {email['subject']}" style="text-decoration: none; color: #4F8BF9;">Reply</a>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Pagination controls
                st.markdown(f"**Page {page_number} of {total_pages}**")
                
                pagination_cols = st.columns(4)
                with pagination_cols[1]:
                    if page_number > 1:
                        prev_page = page_number - 1
                        st.markdown(f'''
                        <a href="?page={prev_page}" target="_self">
                            <button style="background-color:#4F8BF9;color:white;border:none;border-radius:5px;padding:0.5rem 1rem;cursor:pointer;">
                                Previous Page
                            </button>
                        </a>
                        ''', unsafe_allow_html=True)
                
                with pagination_cols[2]:
                    if page_number < total_pages:
                        next_page = page_number + 1
                        st.markdown(f'''
                        <a href="?page={next_page}" target="_self">
                            <button style="background-color:#4F8BF9;color:white;border:none;border-radius:5px;padding:0.5rem 1rem;cursor:pointer;">
                                Next Page
                            </button>
                        </a>
                        ''', unsafe_allow_html=True)
            else:
                st.info("No emails match your current filter criteria.")

# JOBS PAGE
elif page == "Jobs":
    st.header("Job Applications Tracker")
    
    # Check if jobs database exists, initialize if needed
    if not os.path.exists('jobs.xlsx'):
        if initialize_jobs_database():
            st.success("Jobs tracking database has been initialized. You can now start adding job applications.")
        else:
            st.error("Failed to initialize jobs database. Please check the error message above.")
            st.stop()
    
    # Job filters in an expander
    with st.expander("Filters", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            applied_only = st.checkbox("Show only jobs I've applied for")
        with col2:
            status_filter = st.selectbox(
                "Filter by status",
                options=[None, "pending", "interview scheduled", "accepted", "rejected"],
                format_func=lambda x: "All Statuses" if x is None else x.title()
            )
    
    # Try to load job applications
    try:
        jobs_df = load_job_applications(applied_only=applied_only, status_filter=status_filter)
        
        # Job statistics
        if jobs_df is not None and not jobs_df.empty:
            stats = get_application_statistics(jobs_df)
            
            st.subheader("Job Application Statistics")
            
            # Display stats in a nice grid with hover effects
            st.markdown('<div style="display: flex; justify-content: space-between; margin-bottom: 20px;">', unsafe_allow_html=True)
            
            metrics_container = st.container()
            with metrics_container:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Jobs", stats.get('total', 0))
                with col2:
                    st.metric("Applied", stats.get('applied', 0))
                with col3:
                    st.metric("Pending", stats.get('pending', 0))
                with col4:
                    st.metric("Interviews", stats.get('interview scheduled', 0))
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Job applications table
            st.subheader("Job Applications")
            
            # Format for display
            display_df = jobs_df.copy()
            
            # Convert application status to formatted display
            status_icons = {
                "pending": "⏳ Pending",
                "interview scheduled": "🗓️ Interview Scheduled",
                "accepted": "🎉 Accepted",
                "rejected": "❌ Rejected"
            }
            
            if 'application_status' in display_df.columns:
                display_df['application_status'] = display_df['application_status'].map(
                    lambda x: status_icons.get(x, x)
                )
            
            # Convert boolean to yes/no
            if 'user_applied' in display_df.columns:
                display_df['user_applied'] = display_df['user_applied'].map({True: "✅ Yes", False: "❌ No"})
            
            # Rename columns for better display
            display_df = display_df.rename(columns={
                'company_name': 'Company',
                'job_title': 'Position',
                'application_status': 'Status',
                'user_applied': 'Applied',
                'sender_name': 'Contact',
                'sender_email': 'Contact Email'
            })
            
            # Select columns to display
            cols_to_display = ['Company', 'Position', 'Status', 'Applied', 'Contact', 'Contact Email']
            st.dataframe(display_df[cols_to_display], use_container_width=True, height=400)
        else:
            st.info("No job applications found matching your criteria.")
            
            # Show a sample of how it would look
            if not applied_only and status_filter is None:
                st.markdown("""
                ### Getting Started
                
                To add job applications:
                1. Navigate to the **Apply for Job** page
                2. Paste a job description
                3. Submit your application
                
                Or wait for the system to process job-related emails.
                """)
    except Exception as e:
        st.error(f"Error loading job applications: {str(e)}")
        st.info("This could be due to a problem with the jobs.xlsx file structure. Try recreating it or check if it's accessible.")
        
        # Option to recreate the database
        if st.button("Recreate Jobs Database"):
            try:
                # Rename the existing file as backup
                if os.path.exists('jobs.xlsx'):
                    import time
                    timestamp = int(time.time())
                    os.rename('jobs.xlsx', f'jobs_backup_{timestamp}.xlsx')
                    st.info(f"Existing file backed up as jobs_backup_{timestamp}.xlsx")
                
                # Create new database
                if initialize_jobs_database():
                    st.success("Jobs database recreated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to recreate jobs database.")
            except Exception as recreate_error:
                st.error(f"Error recreating database: {str(recreate_error)}")

# APPLY FOR JOB PAGE
elif page == "Apply for Job":
    st.header("Apply for a Job")
    
    # Check if jobs database exists, initialize if needed
    if not os.path.exists('jobs.xlsx'):
        if initialize_jobs_database():
            st.success("Jobs tracking database has been initialized. You can now start applying for jobs.")
        else:
            st.error("Failed to initialize jobs database. Please check the error message above.")
            st.stop()
    
    # Information about the application process
    with st.expander("How it works", expanded=False):
        st.markdown("""
        ### How Job Application Tracking Works
        
        1. **Paste the job description** in the text area below
        2. The system will **extract the company name and job title** automatically
        3. Your application will be **recorded in the job tracker**
        4. You can view and filter your applications in the **Jobs** page
        
        This helps you keep track of all your job applications in one place.
        """)
    
    with st.form("job_application_form", clear_on_submit=False):
        job_description = st.text_area(
            "Paste the job description below:", 
            height=300,
            help="Paste the full job description here. The system will extract the company name and job title."
        )
        
        user_email = st.text_input(
            "Your email (optional):", 
            value="user-applied@example.com",
            help="This is just for record-keeping and won't be used to send emails."
        )
        
        # Custom styling for the submit button
        st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #4F8BF9;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Submit Application", type="primary")
        
        if submitted and job_description:
            if len(job_description.strip()) < 10:
                st.error("Job description is too short. Please provide more information.")
            else:
                try:
                    with st.spinner("Processing your application..."):
                        result = handle_user_job_application(job_description, user_email)
                    
                    if result["success"]:
                        st.success("Application submitted successfully!")
                        
                        # Display result metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Company", result["company"])
                        with col2:
                            st.metric("Position", result["job_title"])
                        with col3:
                            st.metric("Status", result["status"])
                        
                        # Link to jobs page
                        st.markdown("""
                        <form action="." method="get" target="_self">
                            <input type="hidden" name="nav" value="Jobs">
                            <button type="submit" style="background-color:#4F8BF9;color:white;border:none;border-radius:5px;padding:0.5rem 1rem;cursor:pointer;">
                                View all your applications
                            </button>
                        </form>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Failed to process application: {result['message']}")
                except Exception as e:
                    st.error(f"Error processing your application: {str(e)}")
                    st.info("This might be due to an issue with the jobs database. Try navigating to the Jobs page to fix any database issues.")
        elif submitted:
            st.warning("Please enter a job description before submitting.")

# # Add footer with dark theme styling
# st.markdown("""
# ---
# <div style="text-align: center; color: #666; padding: 20px 0 10px 0;">
# Email & Job Tracking System | Built with <span style="color: #4F8BF9;">Streamlit</span>
# </div>
# """, unsafe_allow_html=True)

if __name__ == "__main__":
    # This is needed for deployment in some environments
    pass 