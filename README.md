# Email Tracking System

A smart email processing system powered by LangGraph that automatically categorizes incoming emails, extracts job application details, and provides notifications for urgent messages. Features a Streamlit dashboard for interactive email management.

## Features

- **Email Download**: Automatically downloads emails from your connected account
- **Email Classification**: Categorizes emails into spam, job, urgent, and general
- **Job Application Tracking**: Extracts and organizes job application details
- **Desktop Notifications**: Alerts you about urgent emails
- **Concurrent Processing**: Processes different email categories in parallel
- **Streamlit Dashboard**: Interactive web interface for monitoring and managing emails
- **LangGraph Workflow**: Structured processing pipeline with visualization
- **Agent-Based Architecture**: Modular design with specialized agents for different tasks

## Project Structure

```
email-tracking-system/
├── agents/              # Specialized processing agents
│   ├── classification_agent.py  # Email classification agent
│   ├── summarization_agent.py   # Email summarization agent
│   └── __init__.py
├── core/                # Core system functionality
│   ├── email_downloader.py  # Downloads emails from server
│   ├── email_fetcher.py     # Fetches emails via IMAP
│   ├── initialize_db.py     # Database initialization
│   ├── utils.py            # Utility functions
│   └── __init__.py
├── models/              # Data models
│   ├── email.py         # Email and State type definitions
│   └── __init__.py
├── processing/          # Email processing modules
│   ├── fetch_emails.py    # Fetches unprocessed emails
│   ├── process_all.py     # Concurrent processing of all categories
│   ├── process_general.py # General email processing
│   ├── process_jobs.py    # Job email processing
│   ├── process_spam.py    # Spam email processing
│   ├── process_urgent.py  # Urgent email processing
│   └── __init__.py
├── prompts/             # LLM prompt templates
│   ├── classification_prompt.py # Email classification prompts
│   ├── job_extraction.py       # Job detail extraction prompts
│   ├── summarization_prompt.py # Email summarization prompts
│   └── __init__.py
├── workflows/          # Processing workflows
│   ├── graph_builder.py  # LangGraph workflow definition
│   └── __init__.py
├── jobs/               # Job application management
│   ├── applications.py   # Handle job applications
│   ├── tracker.py        # Track job applications
│   └── viewer.py         # View job applications
├── .streamlit/         # Streamlit configuration
├── app.py              # Streamlit web application
├── main.py             # CLI application entry point
├── config.py           # System configuration
├── apply_for_job.py    # Job application script
├── view_applications.py # View job applications script
├── emails.db           # SQLite database for email storage
├── jobs.xlsx           # Excel file for job application tracking
├── requirements.txt    # Project dependencies
└── README.md           # This file
```

## Architecture

The system follows an agent-based modular architecture:

- **Agents**: Specialized components that perform specific tasks like summarization and classification
- **Processing Modules**: Components that handle specific email categories
- **Workflow**: LangGraph-powered pipeline that orchestrates the entire process
- **Core Services**: Basic functionalities like email downloading and database operations

## Setup

1. Clone the repository:
```
git clone https://github.com/arnnv/email-tracking-system-langgraph
cd email-tracking-system-langgraph
```

2. Create a virtual environment and install dependencies:
```
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your email credentials:
```
IMAP_SERVER=imap.example.com
EMAIL=your-email@example.com
PASSWORD=your-password
OLLAMA_BASE_URL=http://localhost:11434  # If using Ollama
```

4. Run the application:

- For CLI version:
```
python main.py
```

- For web dashboard:
```
streamlit run app.py
```

## Requirements

- Python 3.10+
- Required packages are listed in requirements.txt
- [Ollama](https://ollama.ai/) for running LLMs locally
- IMAP-enabled email account

## How It Works

The system uses a LangGraph-powered workflow with specialized agents:

1. **Email Download**: Connects to your email server and downloads unread emails
2. **Summarization Agent**: Processes and summarizes each email to extract key information 
3. **Classification Agent**: Analyzes emails and assigns them to one of four categories
4. **Parallel Processing**:
   - **Spam**: Marked as processed and categorized
   - **Job**: Details extracted and stored in jobs.xlsx
   - **Urgent**: Notification sent to desktop and marked as processed
   - **General**: Marked as processed

## Web Dashboard

The Streamlit dashboard provides:
- Email processing workflow visualization
- Job application tracking and management
- Email category filtering and viewing
- Manual processing controls
- System statistics

## License

[MIT License](LICENSE)
