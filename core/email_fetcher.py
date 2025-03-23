import imaplib
import email
from email.header import decode_header
from email.message import Message  # Added this import for type hinting
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
from email.utils import parseaddr  # Added this import to parse email addresses
import re
import html.parser

load_dotenv()

# Environment variables
IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# Create an HTML parser to strip HTML tags
class HTMLStripper(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ''.join(self.text)

def strip_html_tags(html_text):
    """
    Strip HTML tags from text and decode HTML entities.
    
    Args:
        html_text: HTML text to clean
        
    Returns:
        Plain text with HTML tags removed and entities decoded
    """
    if not html_text:
        return ""
        
    # Use the HTML parser to strip tags
    stripper = HTMLStripper()
    stripper.feed(html_text)
    text = stripper.get_text()
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Replace common email separators with newlines
    text = re.sub(r'From:|To:|Subject:|Date:', '\n\\g<0>', text)
    
    return text

def connect_to_email_server(imap_server: str, username: str, password: str) -> imaplib.IMAP4_SSL:
    """Connect to the email server and return the IMAP connection."""
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, password)
        return mail
    except Exception as e:
        raise ConnectionError(f"Failed to connect to email server: {e}")

def select_mailbox(mail: imaplib.IMAP4_SSL, mailbox: str = "inbox") -> None:
    """Select a mailbox (folder) in the email account."""
    mail.select(mailbox)

def search_emails(mail: imaplib.IMAP4_SSL, criteria: str = "ALL") -> List[str]:
    """Search for emails based on criteria and return email UIDs."""
    status, messages = mail.uid("search", None, criteria)
    return messages[0].split() if status == "OK" else []

def decode_email_subject(msg: Message) -> str:
    """Decode email subject to readable format."""
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else "utf-8")
    return subject

def get_email_body(msg: Message) -> str:
    """
    Extract the email body text, handling both plain text and HTML content.
    If HTML content is found, it will be stripped of tags to extract the plain text.
    """
    text_content = ""
    html_content = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
                
            # Try to get the plain text version first
            if content_type == "text/plain":
                body = part.get_payload(decode=True)
                if body:
                    text_content = body.decode(errors='replace')
            
            # Get HTML content as fallback
            elif content_type == "text/html" and not text_content:
                body = part.get_payload(decode=True)
                if body:
                    html_content = body.decode(errors='replace')
    else:
        # Handle non-multipart messages
        content_type = msg.get_content_type()
        body = msg.get_payload(decode=True)
        
        if body:
            decoded_body = body.decode(errors='replace')
            if content_type == "text/plain":
                text_content = decoded_body
            elif content_type == "text/html":
                html_content = decoded_body
    
    # Prefer plain text, but fall back to stripped HTML
    if text_content:
        return text_content
    elif html_content:
        return strip_html_tags(html_content)
    
    return ""  # Return empty string if no suitable body found

def extract_email_details(mail: imaplib.IMAP4_SSL, email_uid: str) -> Dict[str, str]:
    """Extract key details from an email using UID."""
    status, msg_data = mail.uid("fetch", email_uid, "(RFC822)")
    
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            # Parse the message
            msg = email.message_from_bytes(response_part[1])
            
            # Extract key information
            from_name, from_email = parseaddr(msg.get("From", ""))
            return {
                "uid": email_uid.decode() if isinstance(email_uid, bytes) else email_uid,
                "subject": decode_email_subject(msg),
                "from_name": from_name,
                "from_email": from_email,
                "date": msg.get("Date", ""),
                "body": get_email_body(msg)
            }
    
    return {"uid": email_uid, "error": "Failed to parse email"}

def get_emails(imap_server: str, username: str, password: str, 
               count: Optional[int] = None, search_criteria: str = "ALL") -> List[Dict[str, str]]:
    """Retrieve emails and return them in a structured format.
    
    Args:
        imap_server: IMAP server address
        username: Email username
        password: Email password
        count: Number of recent emails to fetch (None for all)
        search_criteria: IMAP search criteria string
    
    Returns:
        List of dictionaries containing email details
    """
    try:
        # Connect to the server
        mail = connect_to_email_server(imap_server, username, password)
        select_mailbox(mail)
        
        # Get email UIDs
        email_uids = search_emails(mail, search_criteria)
        
        # Limit number of emails if requested
        if count is not None:
            email_uids = email_uids[-count:] if email_uids else []
        
        # Extract email details
        emails = [extract_email_details(mail, email_uid) for email_uid in email_uids]
        
        # Clean up
        mail.logout()
        
        return emails
    
    except Exception as e:
        print(f"Error: {e}")
        return []
    
if __name__ == "__main__":
    # Example usage: Get the 5 most recent emails
    recent_emails = get_emails(imap_server=IMAP_SERVER, username=EMAIL, password=PASSWORD, count=5)

    # Display emails in a structured format
    for i, email_data in enumerate(recent_emails, 1):
        print(f"\n--- Email {i} ---")
        print(f"UID: {email_data.get('uid', 'Unknown')}")
        print(f"From Name: {email_data.get('from_name', 'Unknown')}")
        print(f"From Email: {email_data.get('from_email', 'Unknown')}")
        print(f"Subject: {email_data.get('subject', 'No subject')}")
        print(f"Date: {email_data.get('date', 'Unknown')}")
        print(f"\nPreview: {email_data.get('body', '').strip()[:500]}")  # Show only first 500 chars for preview