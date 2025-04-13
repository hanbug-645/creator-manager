import os
import time
from dotenv import load_dotenv
from src.gmail_client import GmailClient
from src.ai_engine import AIEngine
from src.database import EmailDatabase, EmailAction
import logging
from datetime import datetime
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Target email to monitor
TARGET_EMAIL = "chengyuan1215@gmail.com"

def setup():
    """Initialize the application"""
    # Load .env file from the config directory
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
    load_dotenv(dotenv_path)
    
    # Check for required environment variables
    required_vars = ['OPENAI_API_KEY', 'MAX_EMAILS_PER_BATCH', 'RESPONSE_DELAY']
    for var in required_vars:
        if not os.getenv(var):
            raise EnvironmentError(f"Missing required environment variable: {var}")
    
    # Initialize database
    db = EmailDatabase()
    
    return (
        int(os.getenv('MAX_EMAILS_PER_BATCH', 10)),
        int(os.getenv('RESPONSE_DELAY', 5)),
        db
    )

def display_emails(emails):
    """Display email subjects in console"""
    if emails:
        logger.info("\n=== New Emails ===")
        for i, email in enumerate(emails, 1):
            logger.info(f"{i}. From: {email['from']}")
            logger.info(f"   Subject: {email['subject']}")
            logger.info("---")
    else:
        logger.info("No new emails to process")

def process_email(gmail_client: GmailClient, ai_engine: AIEngine, email: Dict, db: EmailDatabase):
    """Process a single email"""
    try:
        logger.info(f"Processing email: {email['subject']}")
        
        # Generate AI response and possibly an image
        response, image_path, action = ai_engine.generate_response(email)
        
        # Save to database with initial action
        db.add_email(email['subject'], action or EmailAction.PENDING)
        
        # Validate response
        if not ai_engine.validate_response(response):
            logger.warning(f"Invalid response generated for email {email['id']}")
            return
        
        # Send response with optional image
        success = gmail_client.send_email(
            to=email['from'],
            subject=f"Re: {email['subject']}",
            body=response,
            image_path=image_path
        )
        
        if success:
            logger.info(f"Successfully responded to email {email['id']}")
            # Mark email as read after successful response
            gmail_client.mark_as_read(email['id'])
            
            # Clean up image file if it exists
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"Cleaned up generated image: {image_path}")
        else:
            logger.error(f"Failed to send response for email {email['id']}")

    except Exception as e:
        logger.error(f"Error processing email {email['id']}: {str(e)}")

def process_emails(gmail_client: GmailClient, ai_engine: AIEngine, db: EmailDatabase):
    """Process emails and generate responses"""
    try:
        # Get new emails from target sender
        emails = gmail_client.get_new_emails(target_email=TARGET_EMAIL)
        
        # Display emails in console
        display_emails(emails)
        
        for email in emails:
            process_email(gmail_client, ai_engine, email, db)
            # Add delay between processing emails
            time.sleep(int(os.getenv('RESPONSE_DELAY', 5)))
                
    except Exception as e:
        logger.error(f"Error in process_emails: {str(e)}")

def main():
    try:
        # Setup application
        max_emails, response_delay, db = setup()
        
        # Initialize clients
        gmail_client = GmailClient()
        ai_engine = AIEngine(
            api_key=os.getenv('OPENAI_API_KEY'),
            instructions_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'instructions.txt')
        )
        
        # Create generated_images directory
        os.makedirs("generated_images", exist_ok=True)
        
        # Authenticate Gmail
        logger.info("Authenticating with Gmail...")
        gmail_client.authenticate()
        logger.info("Authentication successful")
        
        logger.info(f"Starting email monitoring for: {TARGET_EMAIL}")
        logger.info("Press Ctrl+C to stop")
        
        logger.info("Starting email monitoring...")
        
        while True:
            process_emails(gmail_client, ai_engine, db)
            time.sleep(response_delay)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
