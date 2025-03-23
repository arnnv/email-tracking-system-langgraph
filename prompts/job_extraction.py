import re
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

def get_job_extraction_examples():
    """
    Returns the examples for job extraction
    """
    return [
        {
            "subject": "Interview Request - Software Engineer at Google",
            "summary": "The company has reviewed the application for Software Engineer position at Google and would like to schedule an interview next week.",
            "output": """Company Name: Google
Job Title: Software Engineer
Application Status: interview scheduled"""
        },
        {
            "subject": "Application Update from Tesla Inc.",
            "summary": "Acknowledgment of application to Tesla Inc. with a note that they will review it and respond soon.",
            "output": """Company Name: Tesla Inc.
Job Title: Unknown Job Title
Application Status: pending"""
        },
        {
            "subject": "Congratulations! Job offer for Marketing Position",
            "summary": "Amazon has offered the Marketing Manager position and requested a review of the attached offer letter.",
            "output": """Company Name: Amazon
Job Title: Marketing Manager
Application Status: accepted"""
        },
        {
            "subject": "Regarding your application to Microsoft",
            "summary": "Microsoft has decided to move forward with other candidates for the Software Developer position.",
            "output": """Company Name: Microsoft
Job Title: Software Developer
Application Status: rejected"""
        },
        {
            "subject": "Mercari: Application Summary for Software Engineering Intern",
            "summary": "Summary of application for Software Engineering Intern position at Mercari in Bangalore starting June 2023.",
            "output": """Company Name: Mercari
Job Title: Software Engineering Intern
Application Status: pending"""
        }
    ]

def get_job_extraction_prompt():
    """
    Returns the prompt for extracting job details from emails
    """
    examples = get_job_extraction_examples()
    
    job_example_prompt = ChatPromptTemplate.from_messages([
        ("human", "Subject: <subject>{subject}</subject>\n\nSummary: <summary>{summary}</summary>"),
        ("ai", "{output}")
    ])

    job_few_shot_prompt = FewShotChatMessagePromptTemplate(
        examples=examples,
        example_prompt=job_example_prompt,
    )

    return ChatPromptTemplate.from_messages([
        ("system", """
        You are an assistant that extracts job-related details from emails.
        Given the subject and summary of an email, extract the following in key-value pair format:

        - Company Name: <company>
        - Job Title: <title>
        - Application Status: <status>

        The `Application Status` must be one of:
        - pending
        - interview scheduled
        - accepted
        - rejected

        If unsure, default to "pending".

        ⚠️ IMPORTANT: 
        - Return ONLY the three key-value pairs in the exact format shown
        - DO NOT include any additional text, explanations, or analysis
        - If you can't extract specific information, use "Unknown Company" or "Unknown Job Title"
        - Always include all three fields, even if some values are unknown
        """),
        job_few_shot_prompt,
        ("human", "Subject: <subject>{subject}</subject>\n\nSummary: <summary>{summary}</summary>")
    ])

def parse_key_value_pairs(text):
    """Parse key-value pairs from text format."""
    parsed_data = {}

    pattern = r"(Company Name|Job Title|Application Status)\s*[:|-]\s*(.*?)(?=\n\s*(?:Company Name|Job Title|Application Status)|$)"
    matches = re.findall(pattern, text, re.DOTALL)

    for key, value in matches:
        parsed_data[key] = value.strip()

    return parsed_data
