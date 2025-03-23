from typing_extensions import Dict, List, TypedDict

class Email(TypedDict):
    id: int
    subject: str
    body: str
    sender: str
    date: str
    summary: str
    email: str  # Adding email field based on usage in the code

class State(TypedDict, total=False):
    emails: List[Email]
    classified_emails: Dict[str, List[Email]]
    errors: List[str]
    processing_stage: str
    num_emails_to_download: int
