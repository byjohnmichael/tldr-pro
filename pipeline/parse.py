import re
import hashlib
from typing import List, Dict, Optional
from urllib.parse import unquote
from bs4 import BeautifulSoup

from shared.editions import slug_from_from_header, content_type_for_section


def decode_tldr_tracking_url(tracking_url: str) -> str:
    """
    Decodes a TLDR tracking URL back to the canonical URL.
    Format: https://tracking.tldrnewsletter.com/CL0/https:%2F%2Factual.com/...
    """
    try:
        # Find the encoded URL after /CL0/
        match = re.search(r"/CL0/(https?[^/]+)", tracking_url)
        if match:
            return unquote(match.group(1))
    except Exception:
        pass
    return tracking_url


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
    return title.strip()


def is_sponsor(title_text: str) -> bool:
    return "(sponsor)" in title_text.lower()


def make_article_id(edition: str, issue_date: str, section: str, index: int) -> str:
    """Generates a deterministic ID like 'ai-2026-02-20-headlines-001'."""
    section_slug = re.sub(r"[^a-z0-9]+", "-", section.lower()).strip("-")
    return f"{edition}-{issue_date}-{section_slug}-{index:03d}"


def detect_issue_date(soup: BeautifulSoup, edition_slug: str) -> Optional[str]:
    """
    Finds the date from the in-body header like 'TLDR AI 2026-02-20'.
    Returns ISO date string or None.
    """
    # Look for bold text matching "TLDR ... YYYY-MM-DD"
    for tag in soup.find_all(["b", "strong"]):
        text = tag.get_text(strip=True)
        match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if match:
            return match.group(1)
    return None


def parse_email(from_header: str, html: str) -> List[Dict]:
    """
    Parses one TLDR newsletter HTML into a list of article dicts.
    Skips sponsor articles.
    """
    edition_slug = slug_from_from_header(from_header)
    if not edition_slug:
        print(f"  WARNING: Unrecognized edition from: {from_header!r}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    issue_date = detect_issue_date(soup, edition_slug) or "unknown"

    articles = []
    current_section = "General"
    section_index = {}  # section -> running count

    # Walk all table cells — sections and articles are adjacent cells in the email structure.
    # Strategy: find bold/large section headers, then collect article links + blurbs that follow.
    all_cells = soup.find_all("td")

    i = 0
    while i < len(all_cells):
        cell = all_cells[i]
        cell_text = cell.get_text(separator=" ", strip=True)

        # Detect section header: bold text, no links, matches known section names
        bold = cell.find(["b", "strong"])
        links_in_cell = cell.find_all("a")
        if bold and not links_in_cell and len(cell_text) < 80:
            section_candidate = cell_text.strip()
            # Must be a plausible section name (short, no punctuation clutter)
            if re.match(r"^[A-Z][A-Za-z &]+$", section_candidate):
                current_section = section_candidate
                i += 1
                continue

        # Detect article cell: contains an <a> tag with a TLDR tracking URL and a blurb
        for link in links_in_cell:
            href = link.get("href", "")
            if "tracking.tldrnewsletter.com" not in href:
                continue

            title_raw = link.get_text(separator=" ", strip=True)

            # Skip navigation links (Sign Up, Advertise, View Online, etc.)
            nav_keywords = ["sign up", "advertise", "view online", "unsubscribe",
                            "manage your subscriptions", "track your referrals",
                            "refer.tldr.tech", "sparklp.co"]
            if any(kw in title_raw.lower() or kw in href.lower() for kw in nav_keywords):
                continue

            # Skip sponsor articles
            if is_sponsor(title_raw):
                continue

            # Skip empty / very short titles
            if len(title_raw) < 10:
                continue

            canonical_url = decode_tldr_tracking_url(href)
            minutes_read = extract_minutes_read(title_raw)
            title = clean_title(title_raw)

            # Blurb: sibling <span> after the <a> within the same outer <span>
            # Structure: <span><a>Title</a><br><br><span>Blurb text.</span></span>
            blurb = ""
            for sibling in link.find_next_siblings("span"):
                candidate = sibling.get_text(separator=" ", strip=True)
                if candidate and len(candidate) > 20:
                    blurb = candidate
                    break

            # Index per section for deterministic IDs
            section_index[current_section] = section_index.get(current_section, 0) + 1
            idx = section_index[current_section]

            articles.append({
                "id": make_article_id(edition_slug, issue_date, current_section, idx),
                "edition": edition_slug,
                "issue_date": issue_date,
                "section": current_section,
                "section_content_type": content_type_for_section(current_section),
                "title": title,
                "blurb": blurb,
                "canonical_url": canonical_url,
                "minutes_read": minutes_read,
                "is_sponsor": False,
            })

        i += 1

    # Deduplicate by canonical_url within this email
    seen_urls = set()
    unique = []
    for article in articles:
        url = article["canonical_url"]
        if url not in seen_urls:
            seen_urls.add(url)
            unique.append(article)

    return unique


def parse_all_emails(raw_emails: List[tuple]) -> List[Dict]:
    """
    Parses all fetched (from_address, html) tuples into a flat list of articles.
    Deduplicates across editions by canonical_url.
    """
    all_articles = []
    seen_urls = set()

    for from_address, html in raw_emails:
        parsed = parse_email(from_address, html)
        print(f"  Parsed {len(parsed)} articles from: {from_address}")
        for article in parsed:
            url = article["canonical_url"]
            if url not in seen_urls:
                seen_urls.add(url)
                all_articles.append(article)

    print(f"  Total unique articles: {len(all_articles)}")
    return all_articles
