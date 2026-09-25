"""
TLDR Pro — daily personalized digest.

    python -m digest.main                 # fetch today's issues, curate, send
    python -m digest.main --dry-run       # same, but write out/digest.html instead of sending
    python -m digest.main --date 2026-09-24
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv

from digest.curate import curate_for_user
from digest.editions import ALL_SLUGS
from digest.fetch import fetch_articles
from digest.render import render_digest
from digest.send import send_digest

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "out" / "digest.html"


def load_config() -> dict:
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f) or {}


def run(issue_date: str, dry_run: bool = False) -> None:
    config = load_config()
    preferences = config.get("preferences") or {}
    to_email = os.environ.get("TO_EMAIL") or config.get("to_email")

    print(f"TLDR Pro — issue date {issue_date}")

    print("\n[1/4] Fetching issues from tldr.tech...")
    articles = fetch_articles(preferences.get("editions") or ALL_SLUGS, issue_date)
    if not articles:
        print("  No issues published for this date (weekend/holiday). Nothing to send.")
        return

    print(f"\n[2/4] Curating {len(articles)} articles with Claude Haiku...")
    curation = curate_for_user(articles, preferences)
    by_id = {a["id"]: a for a in articles}
    selected = [by_id[i] for i in curation["selected_ids"]]
    print(f"  Selected {len(selected)}. Intro: {curation['intro']}")

    print("\n[3/4] Rendering...")
    subject, html = render_digest(selected, curation["intro"], issue_date)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(html)
    print(f"  Wrote {OUTPUT_PATH.relative_to(ROOT)}")

    if dry_run:
        print("\n[4/4] Dry run — not sending.")
        return

    if not to_email:
        sys.exit("ERROR: set to_email in config.yaml (or TO_EMAIL env var)")
    print(f"\n[4/4] Sending to {to_email}...")
    if not send_digest(to_email, subject, html):
        sys.exit(1)
    print("  Sent.")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Send today's personalized TLDR digest.")
    parser.add_argument("--dry-run", action="store_true", help="render to out/digest.html, don't send")
    parser.add_argument("--date", help="issue date YYYY-MM-DD (default: today, US Eastern)")
    args = parser.parse_args()

    # TLDR publishes on US Eastern mornings
    issue_date = args.date or datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    run(issue_date, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
