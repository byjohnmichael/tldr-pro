"""
Fetches TLDR issues from the public web archive at https://tldr.tech/{edition}/{YYYY-MM-DD}
and parses them into article dicts.
"""

import re
from typing import Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup, Tag

from digest.editions import content_type_for_section

BASE_URL = "https://tldr.tech"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; tldr-pro personal digest)"}


class ParseError(Exception):
    """The page loaded but no articles could be found — the site layout probably changed."""


def issue_url(edition: str, issue_date: str) -> str:
    return f"{BASE_URL}/{edition}/{issue_date}"


def extract_minutes_read(title_text: str) -> Optional[int]:
    """Extracts read time from title text like 'Some Title (5 minute read)'."""
    match = re.search(r"\((\d+)\s+minute\s+read\)", title_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def clean_title(title_text: str) -> str:
    """Removes the read time annotation and extra whitespace from a title."""
    title = re.sub(r"\s*\(\d+\s+minute\s+read\)", "", title_text, flags=re.IGNORECASE)
    title = re.sub(r"\s*\(GitHub Repo\)", "", title, flags=re.IGNORECASE)
    return " ".join(title.split())


def is_sponsor(title_text: str) -> bool:
    return "(sponsor)" in title_text.lower()


def make_article_id(edition: str, issue_date: str, section: str, index: int) -> str:
    """Generates a deterministic ID like 'ai-2026-02-20-headlines-001'."""
    section_slug = re.sub(r"[^a-z0-9]+", "-", section.lower()).strip("-")
    return f"{edition}-{issue_date}-{section_slug}-{index:03d}"


def strip_tracking(url: str) -> str:
    """Drops utm_* query params so the same link from two editions dedupes."""
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_")]
    return urlunsplit(parts._replace(query=urlencode(query)))


def _section_for(article: Tag) -> str:
    """Nearest heading above the article that isn't itself inside an article."""
    for heading in article.find_all_previous(["h2", "h3"]):
        if heading.find_parent("article") is None:
            text = heading.get_text(" ", strip=True)
            if text and not re.search(r"\d{4}-\d{2}-\d{2}", text):
                return text
    return "General"


def parse_issue(html: str, edition: str, issue_date: str) -> List[Dict]:
    """Parses one tldr.tech issue page into article dicts. Sponsors are skipped."""
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    counters: Dict[str, int] = {}

    for node in soup.find_all("article"):
        link = node.find("a", href=True)
        if not link:
            continue
        raw_title = link.get_text(" ", strip=True)
        if not raw_title or is_sponsor(raw_title):
            continue

        section = _section_for(node)
        counters[section] = counters.get(section, 0) + 1

        body = node.find(class_="newsletter-html")
        if body is not None:
            blurb = body.get_text(" ", strip=True)
        else:
            link.extract()
            blurb = node.get_text(" ", strip=True)

        articles.append({
            "id":                   make_article_id(edition, issue_date, section, counters[section]),
            "edition":              edition,
            "issue_date":           issue_date,
            "section":              section,
            "section_content_type": content_type_for_section(section),
            "title":                clean_title(raw_title),
            "blurb":                blurb,
            "canonical_url":        strip_tracking(link["href"]),
            "minutes_read":         extract_minutes_read(raw_title),
            "is_sponsor":           False,
        })

    return articles


def fetch_issue_html(edition: str, issue_date: str) -> Optional[str]:
    """Returns the issue page HTML, or None if that edition has no issue on that date."""
    resp = requests.get(issue_url(edition, issue_date), headers=HEADERS, timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    # tldr.tech may redirect a missing date to the edition's latest issue or homepage
    if issue_date not in resp.url:
        return None
    return resp.text


def fetch_articles(editions: List[str], issue_date: str) -> List[Dict]:
    """Fetches and parses every requested edition for a date. Dedupes by URL across editions."""
    articles: List[Dict] = []
    seen_urls = set()

    for edition in editions:
        html = fetch_issue_html(edition, issue_date)
        if html is None:
            print(f"  {edition}: no issue")
            continue

        parsed = parse_issue(html, edition, issue_date)
        if not parsed:
            raise ParseError(
                f"{issue_url(edition, issue_date)} loaded but no articles were found — "
                "tldr.tech's page layout may have changed (see digest/fetch.py)."
            )

        fresh = 0
        for article in parsed:
            if article["canonical_url"] not in seen_urls:
                seen_urls.add(article["canonical_url"])
                articles.append(article)
                fresh += 1
        print(f"  {edition}: {fresh} articles")

    return articles

# byjohnmichael*
