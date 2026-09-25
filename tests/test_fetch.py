from pathlib import Path

from digest.fetch import parse_issue, strip_tracking

FIXTURE = Path(__file__).parent / "fixtures" / "ai-sample.html"


def parse():
    return parse_issue(FIXTURE.read_text(), "ai", "2026-09-24")


def test_parses_articles_and_skips_sponsors():
    titles = [a["title"] for a in parse()]
    assert "Big Lab Ships New Model" in titles
    assert "example/repo" in titles
    assert not any("Sponsor" in t for t in titles)


def test_article_fields():
    first = parse()[0]
    assert first["id"] == "ai-2026-09-24-headlines-launches-001"
    assert first["section"] == "Headlines & Launches"
    assert first["section_content_type"] == "breakthroughs"
    assert first["minutes_read"] == 4
    assert first["canonical_url"] == "https://example.com/model-launch"
    assert first["blurb"] == "A new frontier model with longer context is out."


def test_sections_come_from_headings():
    sections = {a["title"]: a["section"] for a in parse()}
    assert sections["example/repo"] == "Quick Links"


def test_strip_tracking_keeps_other_params():
    assert strip_tracking("https://x.com/a?utm_source=t&ref=y") == "https://x.com/a?ref=y"


def test_fetch_articles_dedupes_and_skips_missing_issues(monkeypatch):
    import digest.fetch as fetch

    html = FIXTURE.read_text()
    monkeypatch.setattr(fetch, "fetch_issue_html", lambda ed, d: html if ed in ("ai", "dev") else None)
    articles = fetch.fetch_articles(["ai", "dev", "tech"], "2026-09-24")
    urls = [a["canonical_url"] for a in articles]
    assert len(urls) == len(set(urls)) == 2


def test_empty_page_raises(monkeypatch):
    import pytest
    import digest.fetch as fetch

    monkeypatch.setattr(fetch, "fetch_issue_html", lambda ed, d: "<html><body>redesigned</body></html>")
    with pytest.raises(fetch.ParseError):
        fetch.fetch_articles(["ai"], "2026-09-24")
