"""
Quick test: fetch + parse, then print a summary.
Run: python -m test_fetch_parse
"""

import os
from dotenv import load_dotenv

load_dotenv()

from pipeline.fetch import fetch_tldr_emails
from pipeline.parse import parse_all_emails


def main():
    print("Fetching TLDR emails from iCloud...")
    raw_emails = fetch_tldr_emails()
    print(f"\nEmails received: {len(raw_emails)}")

    if not raw_emails:
        print("No emails found. Nothing to parse.")
        return

    # Dump first email HTML for debugging
    from_addr, html = raw_emails[0]
    dump_path = os.path.join(os.path.dirname(__file__), "debug_email.html")
    with open(dump_path, "w") as f:
        f.write(html)
    print(f"\nDumped first email HTML to: {dump_path}")
    print(f"  From: {from_addr}")
    print(f"  HTML length: {len(html)} chars")
    print(f"  First 300 chars: {html[:300]!r}")

    print("\nParsing articles...")
    articles = parse_all_emails(raw_emails)
    print(f"\nTotal articles parsed: {len(articles)}")

    # Breakdown by edition
    editions = {}
    for a in articles:
        editions.setdefault(a["edition"], []).append(a)

    print("\n--- Breakdown by edition ---")
    for edition, items in sorted(editions.items()):
        print(f"  {edition}: {len(items)} articles")

    # Print a few sample articles
    print("\n--- Sample articles ---")
    for a in articles[:5]:
        print(f"\n  [{a['edition'].upper()}] {a['title']}")
        if a["blurb"]:
            print(f"  {a['blurb'][:200]}")
        if a["minutes_read"]:
            print(f"  ({a['minutes_read']} min read)")
        print(f"  {a['canonical_url']}")


if __name__ == "__main__":
    main()
