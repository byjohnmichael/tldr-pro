from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from datetime import datetime
import imaplib
import smtplib
import email

# Manages IMAP and SMTP connections with reusable helper methods.
class MailClient:
    def __init__(self, settings):
        self.settings = settings
        self.imap = None
        self.smtp = None
    
    # Logs in to both IMAP and SMTP servers.
    def login(self) -> bool:
        try:
            # IMAP login
            self.imap = imaplib.IMAP4_SSL(self.settings.imap_host, self.settings.imap_port)
            self.imap.login(self.settings.email, self.settings.app_password)
            
            # SMTP login
            self.smtp = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)
            self.smtp.starttls()
            self.smtp.login(self.settings.email, self.settings.app_password)
            
            return True
        except Exception as e:
            print(f"ERROR: Login failed: {e}")
            self.logout()
            return False
            
    # Logs out of both IMAP and SMTP servers.
    def logout(self):
        try:
            if self.imap:
                self.imap.logout()
            if self.smtp:
                self.smtp.quit()
        except Exception as e:
            print(f"ERROR: Logout failed: {e}")

        # Reset IMAP and SMTP connections
        self.imap = None
        self.smtp = None
    
    # Grabs list of email UIDs from the folder within a date range
    def search_emails(self, start_date: datetime, end_date: datetime) -> List[str]:
        if not self.imap:
            raise RuntimeError("Not logged in. Call login() first.")
        
        # Select the folder
        status, _ = self.imap.select(self.settings.folder, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Could not select folder: {self.settings.folder}")
        
        # Build search criteria
        start_str = start_date.strftime("%d-%b-%Y")
        end_str = end_date.strftime("%d-%b-%Y")
        
        # Search for emails from tldrnewsletter.com within date range
        from_domain = "tldrnewsletter.com"
        search_criteria = f'(FROM "@{from_domain}" SINCE {start_str} BEFORE {end_str})'
        
        # Try UID search (more reliable)
        status, data = self.imap.uid("search", None, search_criteria)
        if status != "OK" or not data or not data[0]:
            return []
        
        # Parse UIDs
        uids = data[0].split()
        return [uid.decode() for uid in uids]
    
    # Fetches the HTML content of an email by UID
    def fetch_email_html(self, uid: str) -> Optional[str]:
        if not self.imap:
            raise RuntimeError("Not logged in. Call login() first.")
        
        # Fetch the email
        status, data = self.imap.uid("fetch", uid.encode(), "(RFC822)")
        if status != "OK" or not data:
            return None
        
        # Extract the raw email bytes
        raw_email = data[0][1] if isinstance(data[0], tuple) else data[0]
        if not raw_email:
            return None
        
        # Parse the email
        msg = email.message_from_bytes(raw_email)
        
        # Find HTML part
        html_content = None
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            
            # Skip attachments
            if "attachment" in content_disposition.lower():
                continue
            
            # Get HTML part
            if content_type == "text/html":
                html_content = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return html_content.decode(charset, errors="replace")
        
        # Fallback to plain text if no HTML
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                text_content = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return text_content.decode(charset, errors="replace")
        
        return None
    
    # Deletes emails by UID
    def delete_emails(self, uids: List[str]) -> bool:
        if not self.imap:
            raise RuntimeError("Not logged in. Call login() first.")
        
        if not uids:
            return True
        
        try:
            # Re-select folder in read-write mode
            self.imap.select(self.settings.folder, readonly=False)
            
            # Delete each email
            for uid in uids:
                self.imap.uid("store", uid.encode(), "+FLAGS", "\\Deleted")
            
            # Expunge (permanently delete)
            self.imap.expunge()
            return True
        except Exception as e:
            print(f"Error deleting emails: {e}")
            return False
    
    def send_email(self, subject: str, html_content: str, to_address: Optional[str] = None) -> bool:
        """
        Send an email with HTML content.
        
        Args:
            subject: Email subject
            html_content: HTML body content
            to_address: Recipient (defaults to settings.to_alias)
        
        Returns:
            True if successful
        """
        if not self.smtp:
            raise RuntimeError("Not logged in. Call login() first.")
        
        to_address = to_address or self.settings.to_alias
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.settings.from_alias
            msg["To"] = to_address
            msg["Subject"] = subject
            
            # Add HTML part
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)
            
            # Send
            self.smtp.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.login()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-close connections."""
        self.logout()