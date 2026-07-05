from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import imaplib
import email
import os


class MailClient:
    """Manages iCloud IMAP connection for fetching TLDR newsletters."""

    def __init__(self):
        self.imap_host = os.environ["ICLOUD_IMAP_HOST"]
        self.imap_port = int(os.environ.get("ICLOUD_IMAP_PORT", "993"))
        self.email_address = os.environ["ICLOUD_EMAIL"]
        self.app_password = os.environ["ICLOUD_APP_PASSWORD"]
        self.folder = os.environ.get("ICLOUD_FOLDER", "TLDR")
        self.imap = None

    def login(self) -> bool:
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            self.imap.login(self.email_address, self.app_password)
            return True
        except Exception as e:
            print(f"ERROR: IMAP login failed: {e}")
            self.imap = None
            return False

    def logout(self):
        try:
            if self.imap:
                self.imap.logout()
        except Exception:
            pass
        self.imap = None

    def search_emails(self, start_date: datetime, end_date: datetime) -> List[str]:
        """Returns UIDs of TLDR emails received within the date range."""
        if not self.imap:
            raise RuntimeError("Not logged in.")

        status, _ = self.imap.select(self.folder, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Could not select folder: {self.folder}")

        start_str = start_date.strftime("%d-%b-%Y")
        end_str = end_date.strftime("%d-%b-%Y")
        search_criteria = f'(FROM "@tldrnewsletter.com" SINCE {start_str} BEFORE {end_str})'

        status, data = self.imap.uid("search", None, search_criteria)
        if status != "OK" or not data or not data[0]:
            return []

        uids = data[0].split()
        return [uid.decode() for uid in uids]

    def fetch_email_html(self, uid: str) -> Optional[Tuple[str, str]]:
        """
        Returns (from_address, html_content) for the given UID.
        Falls back to plain text if no HTML part found.
        """
        if not self.imap:
            raise RuntimeError("Not logged in.")

        status, data = self.imap.uid("fetch", uid, "(BODY.PEEK[])")
        if status != "OK" or not data:
            return None

        raw_email = None
        for item in data:
            if isinstance(item, tuple) and len(item) == 2:
                raw_email = item[1]
                break
        if not raw_email:
            return None

        msg = email.message_from_bytes(raw_email)
        from_address = msg.get("From", "")

        for part in msg.walk():
            if "attachment" in str(part.get("Content-Disposition", "")).lower():
                continue
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return from_address, payload.decode(charset, errors="replace")

        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return from_address, payload.decode(charset, errors="replace")

        return None

    def trash_emails(self, uids: List[str]) -> bool:
        """
        Moves emails to iCloud Trash.
        On iCloud, marking \Deleted and expunging moves to "Deleted Messages".
        """
        if not uids:
            return True
        try:
            self.imap.select(self.folder, readonly=False)
            for uid in uids:
                self.imap.uid("store", uid, "+FLAGS", "\\Deleted")
            self.imap.expunge()
            return True
        except Exception as e:
            print(f"ERROR: Trash failed: {e}")
            return False

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, *args):
        self.logout()


def fetch_tldr_emails() -> Tuple[List[Tuple[str, str]], List[str]]:
    """
    Connects to iCloud, grabs all TLDR emails from the past 24 hours.

    Returns:
        (emails, uids)
        emails — list of (from_address, html_content) tuples
        uids   — list of IMAP UIDs for the same emails (used for trashing later)
    """
    now = datetime.now()
    start = now - timedelta(hours=24)

    emails = []
    fetched_uids = []

    with MailClient() as client:
        if not client.imap:
            print("ERROR: Could not connect to iCloud IMAP.")
            return [], []

        uids = client.search_emails(start, now)
        print(f"  Found {len(uids)} TLDR email(s) in the past 24 hours.")

        for uid in uids:
            result = client.fetch_email_html(uid)
            if result:
                emails.append(result)
                fetched_uids.append(uid)
            else:
                print(f"  WARNING: Could not fetch HTML for UID {uid}")

    return emails, fetched_uids


def trash_fetched_emails(uids: List[str]) -> bool:
    """
    Opens a fresh iCloud connection and moves the given UIDs to Trash.
    Call this after all users have been processed.
    """
    if not uids:
        return True

    with MailClient() as client:
        if not client.imap:
            print("ERROR: Could not connect to iCloud IMAP for trash.")
            return False
        return client.trash_emails(uids)
