from database import EmailDatabase, EmailAction
from datetime import datetime

def test_database():
    # Initialize database
    db = EmailDatabase("test_emails.db")

    # Add some test emails
    db.add_email(
        "Collaboration Request from Brand X",
        EmailAction.PENDING,
        datetime.now()
    )
    
    db.add_email(
        "Product Review Opportunity",
        EmailAction.NEGOTIATION,
        datetime.now()
    )
    
    db.add_email(
        "Sponsored Post Request",
        EmailAction.REJECTED,
        datetime.now()
    )
    
    db.add_email(
        "Content Creation Partnership",
        EmailAction.ASSET_PROVIDED,
        datetime.now()
    )

    # Get all emails
    print("\nAll emails:")
    for email in db.get_all_emails():
        print(f"ID: {email[0]}, Title: {email[1]}, Action: {email[3]}, Timestamp: {email[2]}")

    # Get pending emails
    print("\nPending emails:")
    pending_emails = db.get_emails_by_action(EmailAction.PENDING)
    for email in pending_emails:
        print(f"ID: {email[0]}, Title: {email[1]}, Timestamp: {email[2]}")

if __name__ == "__main__":
    test_database()
