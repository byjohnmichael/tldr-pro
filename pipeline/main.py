"""
TLDR Pro — Daily Digest Pipeline

Phase 1: Single-user mode (John only).
Run: python -m pipeline.main
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

from pipeline.fetch import fetch_tldr_emails, trash_fetched_emails
from pipeline.parse import parse_all_emails
from pipeline.curate import curate_for_user
from pipeline.render import render_digest
from pipeline.send import send_digest


# --- Phase 1: hardcoded single-user config ---
# In Phase 3 this will be replaced by loading users from Supabase.
PHASE1_USER = {
    "email":            os.environ.get("TO_EMAIL", ""),
    "user_token":       "phase1-user",       # placeholder until DB exists
    "unsubscribe_token": "phase1-unsub",     # placeholder until DB exists
    "preferences": {
        "editions":            ["tech", "dev", "ai", "infosec", "product", "devops",
                                "founders", "design", "marketing", "crypto", "fintech", "data"],
        "content_type":        "both",
        "digest_length":       "medium",
        "interest_tags":       [],
        "exclude_topics":      [],
        "custom_instructions": "",
    },
    "feedback": [],
}


def run(trash: bool = True):
    os.system("clear")
    print("=" * 50)
    print("  TLDR Pro — Daily Digest Pipeline")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. Fetch
    print("\n[1/5] Fetching TLDR emails from iCloud...")
    raw_emails, email_uids = fetch_tldr_emails()
    if not raw_emails:
        print("  No emails found. Nothing to do.")
        sys.exit(0)

    # 2. Parse
    print("\n[2/5] Parsing newsletters...")
    articles = parse_all_emails(raw_emails)
    if not articles:
        print("  No articles parsed. Exiting.")
        sys.exit(0)

    # 3. Curate (Phase 1: single user)
    print("\n[3/5] Curating digest with Claude Haiku...")
    user = PHASE1_USER
    if not user["email"]:
        print("  ERROR: TO_EMAIL not set in .env")
        sys.exit(1)

    curation = curate_for_user(
        articles=articles,
        preferences=user["preferences"],
        feedback=user["feedback"],
    )
    selected_ids = set(curation["selected_ids"])
    intro = curation["intro"]
    selected_articles = [a for a in articles if a["id"] in selected_ids]

    # Preserve AI ordering
    id_order = {article_id: i for i, article_id in enumerate(curation["selected_ids"])}
    selected_articles.sort(key=lambda a: id_order.get(a["id"], 999))

    print(f"  Selected {len(selected_articles)} articles.")
    print(f"  Intro: {intro}")

    # 4. Render
    print("\n[4/5] Rendering email...")
    subject, html = render_digest(
        articles=selected_articles,
        intro=intro,
        user_token=user["user_token"],
        unsubscribe_token=user["unsubscribe_token"],
    )
    print(f"  Subject: {subject}")

    # 5. Send
    print(f"\n[5/5] Sending digest to {user['email']}...")
    success = send_digest(
        to_email=user["email"],
        subject=subject,
        html=html,
    )

    if success:
        print("\n  ✓ Digest sent successfully!")
    else:
        print("\n  ✗ Failed to send digest.")
        sys.exit(1)

    # 6. Trash source emails now that all users have been processed
    if trash:
        print("\n[6/6] Moving source emails to Trash...")
        trashed = trash_fetched_emails(email_uids)
        if trashed:
            print(f"  Moved {len(email_uids)} email(s) to Trash.")
        else:
            print("  WARNING: Could not trash emails. They remain in the TLDR folder.")
    else:
        print("\n[6/6] Skipping trash (trash=False).")

    print("\n" + "=" * 50)
    print("  Pipeline complete.")
    print("=" * 50)


if __name__ == "__main__":
    run()
