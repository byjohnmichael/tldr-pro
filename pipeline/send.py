import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ICLOUD_SMTP_HOST = "smtp.mail.me.com"
ICLOUD_SMTP_PORT = 587


def send_digest(to_email: str, subject: str, html: str) -> bool:
    """
    Sends the digest email via iCloud SMTP.
    Returns True on success.
    """
    from_email = os.environ.get("FROM_EMAIL", "tldr@byjohnmichael.com")
    icloud_email = os.environ["ICLOUD_EMAIL"]
    app_password = os.environ["ICLOUD_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"TLDR Pro <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(ICLOUD_SMTP_HOST, ICLOUD_SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(icloud_email, app_password)
            server.sendmail(from_email, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"  ERROR: Failed to send email to {to_email}: {e}")
        return False
