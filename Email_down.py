import imaplib
import email
from email.header import decode_header
import os
import sys

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

def download_attachments(email_user, password, imap_server, subject_keyword, download_folder):
    """
    Connect to email server, search for emails with the specific subject,
    and download all attachments to the provided folder.
    """
    # Create download folder if it doesn't exist
    os.makedirs(download_folder, exist_ok=True)
    
    # Connect to the IMAP server
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, password)
        mail.select('inbox')  # Change to another folder if needed, e.g., '"Sent"'
    except Exception as e:
        print(f"Failed to connect/login: {e}")
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
    EMAIL_USER = "your_email@gmail.com"  # Your full email address
    EMAIL_PASSWORD = "your_app_password"  # App password from Google
    IMAP_SERVER = "imap.gmail.com"  # For Gmail; Outlook: "outlook.office365.com"
    SUBJECT_KEYWORD = "Your Specific Subject Here"  # Exact subject or keyword
    DOWNLOAD_FOLDER = r"C:\path\to\your\download\folder"  # Full path to save files (use raw string for Windows paths)
    
    download_attachments(EMAIL_USER, EMAIL_PASSWORD, IMAP_SERVER, SUBJECT_KEYWORD, DOWNLOAD_FOLDER)