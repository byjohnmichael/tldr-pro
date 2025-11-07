from datetime import datetime, timedelta
from settings import get_settings
from mail import MailClient
import time
import os

# Main Function
def main():
    os.system("clear")
    print("TLDR Pro")
    print("=" * 50)
    time.sleep(1)

    print("\nLoading settings...")
    time.sleep(0.5)
    settings = get_settings()
    if settings:
        print("Settings loaded successfully!")

    print("\nLogging into email client...")
    time.sleep(0.5)
    mail_client = MailClient(settings)
    if mail_client.login():
        print(f"Email client logged into {settings.email} successfully!")

    print("\nSearching for emails...")
    time.sleep(0.5)
    # Creating date range for the past 24 hours
    now = datetime.now()
    today_11am = now.replace(hour=11, minute=0, second=0, microsecond=0)
    yesterday_11am = today_11am - timedelta(days=1)
    # Searching for emails 
    emails = mail_client.search_emails(yesterday_11am, today_11am)
    if emails:
        print(f"Found {len(emails)} emails!")
    else:
        print("No emails found.")
        return

    print("\nFetching email HTML...")
    time.sleep(0.5)
    for email in emails:
        html = mail_client.fetch_email_html(email)
        if html:
            print(html)
            print(f"HTML fetched successfully for email {email}!")
        else:
            print(f"Failed to fetch HTML for email {email}.")
            return
    
    
        # TODO: Implement workflow steps
    # 1. Connect to IMAP and fetch newsletters
    # 2. Parse newsletters
    # 3. Merge and deduplicate
    # 4. Select best items
    # 5. Render email
    # 6. Send via SMTP
    # 7. Cleanup (delete/archive)

# Entry Point
if __name__ == "__main__":
    main() # By John Michael