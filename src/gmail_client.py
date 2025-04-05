from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict
import time
import mimetypes

class GmailClient:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
        self.creds = None
        self.service = None
        self.processed_ids = set()  # Keep track of processed email IDs

    def authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0"""
        flow = InstalledAppFlow.from_client_secrets_file(
            'config/credentials.json', self.SCOPES)
        self.creds = flow.run_local_server(port=0)
        self.service = build('gmail', 'v1', credentials=self.creds)

    def get_new_emails(self, target_email: str = None) -> List[Dict]:
        """Fetch new unread emails, optionally filtering by sender"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX', 'UNREAD'],
                q=f"from:{target_email}" if target_email else None
            ).execute()
            
            messages = results.get('messages', [])
            new_emails = []
            
            for message in messages:
                if message['id'] not in self.processed_ids:
                    email = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    headers = email['payload']['headers']
                    email_data = {
                        'id': message['id'],
                        'from': next(h['value'] for h in headers if h['name'] == 'From'),
                        'subject': next(h['value'] for h in headers if h['name'] == 'Subject'),
                        'body': self._get_email_body(email),
                        'thread_id': email['threadId']
                    }
                    
                    # Only include emails from target_email if specified
                    if not target_email or target_email in email_data['from']:
                        new_emails.append(email_data)
                        self.processed_ids.add(message['id'])
            
            return new_emails
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []

    def send_email(self, to: str, subject: str, body: str, image_path: str = None) -> bool:
        """Send an email response with optional image attachment"""
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            # Add text body
            msg_text = MIMEText(body)
            message.attach(msg_text)
            
            # Add image attachment if provided
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img_data = f.read()
                    
                image = MIMEImage(img_data)
                image.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                message.attach(image)
            
            # Encode and send
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    def _get_email_body(self, email: Dict) -> str:
        """Extract email body from the email message"""
        if 'parts' in email['payload']:
            for part in email['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    return base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
        elif 'body' in email['payload']:
            return base64.urlsafe_b64decode(
                email['payload']['body']['data']
            ).decode('utf-8')
        return ""

    def mark_as_read(self, email_id: str):
        """Mark an email as read by removing UNREAD label"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            print(f"Error marking email as read: {str(e)}")
