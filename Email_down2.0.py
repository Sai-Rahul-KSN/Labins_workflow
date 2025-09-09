import imaplib
import email
from email.header import decode_header
import os
import base64
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError

# Scopes for Gmail IMAP access (minimal for reading)
SCOPES = ['https://mail.google.com/']

def get_oauth2_token(credentials_file):
    """Get or refresh OAuth2 access token."""
    creds = None
    # Load existing token if available
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If no valid creds, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)  # Opens browser for auth
        # Save for future runs
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds.token  # Returns access token

def generate_xoauth2_string(user, access_token):
    """Generate SASL XOAUTH2 string for IMAP auth."""
    xoauth2 = base64.b64encode(f'user={user}\x01auth=Bearer {access_token}\x01\x01'.encode('utf-8')).decode('utf-8')
    return xoauth2

def decode_mime_words(s):
    """Decode MIME-encoded headers."""
    if isinstance(s, bytes):
        s = s.decode('utf-8', 'ignore')
    decoded_parts = decode_header(s)
    decoded = ''
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            part = part.decode('utf-8', 'ignore')
        if encoding:
            part = part.encode('utf-8').decode(encoding, 'ignore')
        decoded += part
    return decoded.strip()

def download_attachments(email_user, credentials_file, imap_server, subject_keyword, download_folder):
    """
    Connect to email server using OAuth2, search for emails with the specific subject,
    and download all attachments to the provided folder.
    """
    # Create download folder if it doesn't exist
    os.makedirs(download_folder, exist_ok=True)
    
    # Get OAuth2 access token
    try:
        access_token = get_oauth2_token(credentials_file)
        print("OAuth2 token obtained successfully.")
    except Exception as e:
        print(f"Failed to get OAuth2 token: {e}")
        return
    
    # Connect to the IMAP server
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        # Authenticate with XOAUTH2 (no password needed)
        auth_string = generate_xoauth2_string(email_user, access_token)
        mail.authenticate('XOAUTH2', lambda x: auth_string.encode('utf-8'))
        mail.select('inbox')  # Change to another folder if needed
        print("IMAP connection and auth successful.")
    except Exception as e:
        print(f"Failed to connect/auth: {e}")
        return
    
    # Search for emails with the specific subject (case-insensitive)
    search_query = f'(SUBJECT "{subject_keyword}")'
    status, messages = mail.search(None, search_query)
    if status != 'OK':
        print("No messages found matching the subject.")
        mail.close()
        mail.logout()
        return
    
    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} emails with subject containing '{subject_keyword}'.")
    
    for email_id in email_ids:
        # Fetch the email
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        if status != 'OK':
            continue
        
        # Parse the email
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Decode and print subject for verification
        subject = decode_mime_words(msg['Subject'])
        print(f"Processing email with subject: {subject}")
        
        # Walk through email parts to find attachments
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if filename:
                # Decode filename if needed
                filename = decode_mime_words(filename)
                if not filename:
                    filename = 'attachment'  # Fallback name
                
                # Full path to save the file
                filepath = os.path.join(download_folder, filename)
                
                # Avoid overwriting if file exists (add unique suffix)
                counter = 1
                original_path = filepath
                while os.path.exists(filepath):
                    name, ext = os.path.splitext(original_path)
                    filepath = f"{name}_{counter}{ext}"
                    counter += 1
                
                try:
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    print(f"Downloaded: {filename} -> {filepath}")
                except Exception as e:
                    print(f"Error saving {filename}: {e}")
    
    # Cleanup
    mail.close()
    mail.logout()
    print("Download complete!")

if __name__ == "__main__":
    # Configuration - Update these values
    EMAIL_USER = "sairahulk.be22@gmail.com"  # Your full email address
    CREDENTIALS_FILE = "credentials.json"  # Path to your downloaded OAuth JSON
    IMAP_SERVER = "imap.gmail.com"  # For Gmail
    SUBJECT_KEYWORD = "CCRForm"  # Exact subject or keyword
    DOWNLOAD_FOLDER = r"C:\Users\sk23dg\Desktop\Labins_Workflow\Fil_downloader"  # Full path to save files
    
    download_attachments(EMAIL_USER, CREDENTIALS_FILE, IMAP_SERVER, SUBJECT_KEYWORD, DOWNLOAD_FOLDER)