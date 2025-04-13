from database import EmailDatabase, EmailAction
from datetime import datetime
import sqlite3

def format_timestamp(timestamp_str):
    # Parse the ISO format timestamp and format it in a more readable way
    dt = datetime.fromisoformat(timestamp_str)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def create_sample_entries():
    db = EmailDatabase()
    
    # Sample entries
    entries = [
        ("BMW M4 Sponsorship Inquiry", EmailAction.NEGOTIATION),
        ("Toyota Collaboration Request", EmailAction.PENDING),
        ("Mercedes AMG Partnership", EmailAction.ASSET_PROVIDED),
        ("Porsche 911 Review Request", EmailAction.REJECTED),
        ("Tesla Model S Campaign", EmailAction.PENDING)
    ]
    
    for title, action in entries:
        db.add_email(title, action, datetime.now())
    
    print("Created sample entries.")

def show_latest_entries(limit=5):
    db = EmailDatabase()
    
    print("\n=== Latest Email Entries ===")
    print("----------------------------")
    
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        
        # Check if we have any entries
        cursor.execute("SELECT COUNT(*) FROM emails")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("No entries found. Creating sample entries...")
            create_sample_entries()
        
        cursor.execute("""
            SELECT id, title, timestamp, action 
            FROM emails 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        entries = cursor.fetchall()
        
        if not entries:
            print("No entries found in database.")
            return
            
        for entry in entries:
            id, title, timestamp, action = entry
            formatted_time = format_timestamp(timestamp)
            print(f"\nID: {id}")
            print(f"Title: {title}")
            print(f"Time: {formatted_time}")
            print(f"Action: {action}")
            print("----------------------------")

if __name__ == "__main__":
    show_latest_entries()
