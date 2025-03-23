import sqlite3
import config
from core.initialize_db import connect_to_db

def connect_to_db():
    """Connect to the SQLite database"""
    return sqlite3.connect(config.DB_PATH)

def print_db():
    """
    Print the contents of the database in a formatted way
    
    Returns:
        String representation of the database
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
        if not cursor.fetchone():
            return "Database exists but 'emails' table not found."
            
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM emails")
        total = cursor.fetchone()[0]
        
        # Get processed count
        cursor.execute("SELECT COUNT(*) FROM emails WHERE email_processed = 1")
        processed = cursor.fetchone()[0]
        
        # Get counts by category if the category column exists
        cursor.execute("PRAGMA table_info(emails)")
        columns = [info[1] for info in cursor.fetchall()]
        
        category_stats = ""
        if "category" in columns:
            cursor.execute("SELECT category, COUNT(*) FROM emails GROUP BY category")
            categories = cursor.fetchall()
            
            if categories:
                category_stats = "\nCategory breakdown:\n"
                for category, count in categories:
                    cat_display = category if category else "None"
                    category_stats += f"  - {cat_display}: {count}\n"
        
        conn.close()
        
        return f"Total emails: {total}\nProcessed emails: {processed}\nUnprocessed emails: {total - processed}{category_stats}"
    except Exception as e:
        return f"Error accessing database: {str(e)}"
