from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

def get_classification_examples():
    """
    Returns the examples for email classification
    """
    return [
        {
            "subject": "Hurry! Limited Time Offer on Credit Cards",
            "summary": "Promotional email offering 0% interest credit cards with exclusive deals.",
            "sender": "bank@promo.com",
            "category": "spam"
        },
        {
            "subject": "Your Netflix subscription is expiring",
            "summary": "Notification about Netflix subscription expiry in 2 days with a request to update payment information.",
            "sender": "netflix-noreply@accounts.com",
            "category": "spam"
        },
        {
            "subject": "New DC Comics Releases This Week",
            "summary": "Newsletter about latest DC Comics releases including Action Comics #1053 and Justice Society of America #29.",
            "sender": "newsletter@dccomics.com",
            "category": "spam"
        },
        {
            "subject": "Software Engineer Interview - Google",
            "summary": "Invitation for an interview at Google for Software Engineer position with a request for availability next week.",
            "sender": "recruiter@google.com",
            "category": "job"
        },
        {
            "subject": "Application Update: Product Manager Position",
            "summary": "Notification that the company wants to move forward with the Product Manager application after reviewing the resume.",
            "sender": "careers@company.org",
            "category": "job"
        },
        {
            "subject": "Mercari: Application Summary for Software Engineering Intern",
            "summary": "Overview of application details for Software Engineering Intern position at Mercari.",
            "sender": "careers@mercari.com",
            "category": "job"
        },
        {
            "subject": "URGENT: Submit your project by midnight",
            "summary": "Reminder that project submission deadline is today at 11:59 PM.",
            "sender": "professor@university.edu",
            "category": "urgent"
        },
        {
            "subject": "Critical Server Downtime Alert",
            "summary": "Alert about main application server experiencing issues requiring immediate attention.",
            "sender": "alerts@monitoring.com",
            "category": "urgent"
        },
        {
            "subject": "Weekend Football Match",
            "summary": "Team meeting notification for weekend football practice at 5 PM.",
            "sender": "teammate@gmail.com",
            "category": "general"
        },
        {
            "subject": "Meeting Notes from Tuesday",
            "summary": "Shared notes from Tuesday's meeting with an offer to answer any questions.",
            "sender": "colleague@company.com",
            "category": "general"
        },
        {
            "subject": "Product Update",
            "summary": "Information about implemented product improvements based on feedback and upcoming testing of new features.",
            "sender": "arnav.gupta@company.com",
            "category": "general"
        }
    ]

def get_classification_prompt():
    """
    Returns the prompt for classifying emails
    """
    examples = get_classification_examples()
    
    example_prompt = ChatPromptTemplate.from_messages([
        ("human", "Subject: {subject}\n\nSummary: {summary}\n\nSender: {sender}"),
        ("ai", "{category}")
    ])

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
    )

    return ChatPromptTemplate.from_messages([
        ("system", """
        You are an email classifier that MUST categorize each email into EXACTLY ONE of these four categories:
        - spam: Unsolicited emails, advertisements, phishing attempts, newsletters, promotional content
        - job: Job opportunities, interview requests, recruitment-related, application status updates
        - urgent: Time-sensitive matters requiring immediate attention
        - general: Regular correspondence that doesn't fit the above

        ⚠️ IMPORTANT: Your response MUST CONTAIN ONLY ONE WORD - either "spam", "job", "urgent", or "general".
        DO NOT provide any analysis, explanation, or additional text.
        DO NOT use any punctuation marks.
        DO NOT include quotes or formatting.

        Example of correct response: spam
        Example of correct response: job
        Example of correct response: urgent
        Example of correct response: general

        Any other format is incorrect.
        """),
        few_shot_prompt,
        ("human", "Subject: {subject}\n\nSummary: {summary}\n\nSender: {sender}")
    ])
