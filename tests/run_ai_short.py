"""
End-to-end pipeline test: AI edition, short digest, both content types.

Run from the project root:
    python -m tests.run_ai_short

What it does:
    1. Fetches TLDR emails from iCloud (real network call)
    2. Parses all editions, then filters down to AI only
    3. Curates 5 articles via Claude Haiku
    4. Renders the HTML email
    5. Sends to TO_EMAIL (from .env)
    6. Saves the rendered HTML to tests/output/ai_short_latest.html for inspection
"""

import os
import sys
from datetime import datetime

# Ensure project root is on sys.path regardless of how this script is invoked
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from pipeline.fetch import fetch_tldr_emails, trash_fetched_emails
from pipeline.parse import parse_all_emails
from pipeline.curate import curate_for_user
from pipeline.render import render_digest
from pipeline.send import send_digest

# Set to True to trash source emails after a successful test run.
TRASH_AFTER_SEND = False

TEST_PREFERENCES = {
    "editions":            ["ai"],
    "content_type":        "both",
    "digest_length":       "short",   # 5 articles
    "interest_tags":       [],
    "exclude_topics":      [],
    "custom_instructions": "",
}

TEST_USER = {
    "email":             os.environ.get("TO_EMAIL", ""),
    "user_token":        "test-user",
    "unsubscribe_token": "test-unsub",
    "preferences":       TEST_PREFERENCES,
    "feedback":          [],
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def divider(label=""):
    width = 52
    if label:
        pad = (width - len(label) - 2) // 2
        print(f"\n{'─' * pad} {label} {'─' * (width - pad - len(label) - 2)}")
    else:
        print("─" * width)


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 52)
    print("  TLDR Pro — Pipeline Test")
    print("  Preset: AI · Short (5 articles) · Both types")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 52)

    # ── 1. Fetch ──────────────────────────────────────────
    divider("1 / 5  FETCH")
    print("Connecting to iCloud IMAP...")
    raw_emails, email_uids = fetch_tldr_emails()

    if not raw_emails:
        print("\nERROR: No emails fetched. Check iCloud credentials and that the TLDR")
        print("       folder has mail from the past 24 hours.")
        sys.exit(1)

    print(f"\nFetched {len(raw_emails)} email(s)  [UIDs: {', '.join(email_uids)}]:")
    for from_addr, html in raw_emails:
        print(f"  · {from_addr}  ({len(html):,} chars)")

    # ── 2. Parse ──────────────────────────────────────────
    divider("2 / 5  PARSE")
    all_articles = parse_all_emails(raw_emails)

    if not all_articles:
        print("\nERROR: Parsed 0 articles. The HTML structure may have changed.")
        sys.exit(1)

    # Show breakdown by edition
    by_edition: dict = {}
    for a in all_articles:
        by_edition.setdefault(a["edition"], []).append(a)

    print(f"\nTotal articles parsed: {len(all_articles)}")
    print("\nBreakdown by edition:")
    for edition, items in sorted(by_edition.items()):
        marker = " ◀ TEST TARGET" if edition == "ai" else ""
        print(f"  {edition:<12} {len(items):>3} articles{marker}")

    ai_articles = by_edition.get("ai", [])
    if not ai_articles:
        print("\nWARNING: No AI edition articles found today. The edition may not have")
        print("         published, or the parser may not be recognizing it.")
        print("\nAvailable editions: " + ", ".join(sorted(by_edition.keys())))
        sys.exit(1)

    print(f"\nAI edition articles ({len(ai_articles)}):")
    for a in ai_articles:
        read = f"  {a['minutes_read']}m" if a.get("minutes_read") else ""
        print(f"  [{a['section']}] {a['title'][:70]}{read}")

    # ── 3. Curate ─────────────────────────────────────────
    divider("3 / 5  CURATE")
    print("Calling Claude Haiku to select 5 articles...")

    curation = curate_for_user(
        articles=all_articles,
        preferences=TEST_PREFERENCES,
        feedback=[],
    )

    selected_ids = set(curation["selected_ids"])
    intro = curation["intro"]
    selected_articles = [a for a in all_articles if a["id"] in selected_ids]

    # Preserve AI ordering
    id_order = {aid: i for i, aid in enumerate(curation["selected_ids"])}
    selected_articles.sort(key=lambda a: id_order.get(a["id"], 999))

    print(f"\nIntro: {intro}")
    print(f"\nSelected {len(selected_articles)} article(s):")
    for a in selected_articles:
        print(f"  · {a['title'][:70]}")

    if len(selected_articles) == 0:
        print("\nERROR: Haiku returned 0 matching article IDs. Check the curate prompt.")
        sys.exit(1)

    # ── 4. Render ─────────────────────────────────────────
    divider("4 / 5  RENDER")
    subject, html = render_digest(
        articles=selected_articles,
        intro=intro,
        user_token=TEST_USER["user_token"],
        unsubscribe_token=TEST_USER["unsubscribe_token"],
    )

    output_path = os.path.join(OUTPUT_DIR, "ai_short_latest.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Subject: {subject}")
    print(f"HTML saved to: tests/output/ai_short_latest.html  ({len(html):,} chars)")

    # ── 5. Send ───────────────────────────────────────────
    divider("5 / 5  SEND")
    to_email = TEST_USER["email"]
    if not to_email:
        print("ERROR: TO_EMAIL is not set in .env — skipping send.")
        print("       HTML was still saved to tests/output/ai_short_latest.html")
        sys.exit(1)

    print(f"Sending to {to_email}...")
    success = send_digest(to_email=to_email, subject=subject, html=html)

    divider()
    if success:
        print(f"  Test passed. Digest sent to {to_email}.")
        if TRASH_AFTER_SEND:
            trashed = trash_fetched_emails(email_uids)
            if trashed:
                print(f"  Moved {len(email_uids)} source email(s) to Trash.")
            else:
                print("  WARNING: Could not trash source emails.")
        else:
            print(f"  Source emails preserved (TRASH_AFTER_SEND=False).")
    else:
        print("  Test FAILED at send step. Check iCloud SMTP credentials.")
        sys.exit(1)

    print("=" * 52)


if __name__ == "__main__":
    run()
