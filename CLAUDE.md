# TLDR Pro — Claude Context

## What This Project Is

A personal daily digest for John Michael. Every morning a GitHub Actions cron downloads that
day's TLDR issues from the public archive at tldr.tech, uses Claude Haiku to pick the articles
that match the preferences in `config.yaml`, and emails one digest via iCloud SMTP.

It's built to need almost no upkeep: no database, no server, no inbox, no web app. It's
stateless, so each run stands on its own.

**Where it's headed:** today it runs only on GitHub Actions. Later it should also run on a
schedule on a local machine, or as a hosted service. Keep the pipeline (`digest/`) independent
of GitHub Actions. The workflow should stay a thin wrapper around `python -m digest.main`, with
all configuration coming from env vars and `config.yaml`, so moving to another host only means
changing the scheduler.

---

## Layout

```
tldr-pro/
├── config.yaml                  # preferences + to_email (the only thing edited day to day)
├── digest/
│   ├── main.py                  # entry point: python -m digest.main [--dry-run] [--date YYYY-MM-DD]
│   ├── fetch.py                 # GET https://tldr.tech/{edition}/{date} → article dicts
│   ├── curate.py                # Claude Haiku selection
│   ├── render.py                # HTML email
│   ├── send.py                  # iCloud SMTP
│   └── editions.py              # edition slugs/names + section→content_type map
├── tests/
│   ├── test_fetch.py            # parser tests (no network)
│   └── fixtures/ai-sample.html  # SYNTHETIC — replace with a real saved tldr.tech page
├── pytest.ini                   # puts the project root on sys.path for `pytest`
└── .github/workflows/daily.yml  # cron 0 14 * * * (6 AM PST / 7 AM PDT) + manual trigger
```

## Stack
- Python 3.12, requests, BeautifulSoup4, PyYAML
- **AI:** Claude Haiku via headless Claude Code (`claude -p --model haiku`) on the Claude plan — no API key
- **Send:** iCloud SMTP `smtp.mail.me.com:587` STARTTLS, From `tldr@byjohnmichael.com`
- **Scheduler:** GitHub Actions. A failed run emails the repo owner automatically.

## Running

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                        # fill in secrets
python -m digest.main --dry-run             # writes out/digest.html, doesn't send
python -m digest.main                       # sends
pytest -q tests
```

In Actions: the workflow's "Run workflow" button takes an optional date and a dry-run toggle.
The rendered HTML is uploaded as the `digest` artifact on every run.

## Secrets / env vars

| Variable | Purpose |
|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude plan token from `claude setup-token` (not needed locally if logged in) |
| `ICLOUD_EMAIL` | iCloud SMTP login: the Apple ID / `@icloud.com` address, **not** a custom-domain alias (that gives `535 authentication failed`) |
| `ICLOUD_APP_PASSWORD` | App-specific password |
| `FROM_EMAIL` | Optional, defaults to `tldr@byjohnmichael.com` |
| `TO_EMAIL` | Optional override of `to_email` in `config.yaml` |

The first three are GitHub repository secrets; locally they go in `.env`.

## Preferences (`config.yaml`)
`editions`, `content_type` (`breakthroughs`/`stories`/`both`), `digest_length`
(`short` 5 / `medium` 10 / `long` 18), `interest_tags`, `exclude_topics`, `custom_instructions`.

## Fetch / parse notes
- Issue URL: `https://tldr.tech/{slug}/{YYYY-MM-DD}`. The date is today in US Eastern time.
- A 404, or a redirect away from the dated URL, means no issue that day (normal on weekends).
  If nothing at all was published, the run exits 0 without sending.
- A page that loads but yields zero articles raises `ParseError`. The run fails on purpose so
  a tldr.tech redesign triggers a failure email instead of silently sending nothing.
- Each `<article>` is one item: its first link gives the title and URL, and `.newsletter-html`
  (or the leftover text) gives the blurb. The section comes from the nearest `h2`/`h3` above it
  that isn't inside an article.
- `utm_*` params are stripped; articles are deduped by URL across editions; sponsors are skipped.
- The selectors work against the live site (verified by real runs). The test fixture is still
  synthetic, though, so swap in a real saved page when convenient.

## Article schema

```python
{
    "id": "ai-2026-02-20-headlines-launches-001",
    "edition": "ai",
    "issue_date": "2026-02-20",
    "section": "Headlines & Launches",
    "section_content_type": "breakthroughs",
    "title": "Article title",
    "blurb": "One or two sentence summary.",
    "canonical_url": "https://actual-url.com/path",
    "minutes_read": 5,           # None if absent
    "is_sponsor": False,
}
```

## Conventions
- Run from the project root; modules import as `digest.x`.
- Keep it stateless and single-user for now. Don't add a database or server until the move to
  local/hosted running actually calls for it.
- Before sending, `main.run` checks that `to_email` and the iCloud secrets are set, so a
  misconfigured run fails immediately instead of after the fetch and Haiku call.
- Every hand-written source file ends with a blank line and then the signature `byjohnmichael*`
  in that file's comment syntax (`# byjohnmichael*`, `// byjohnmichael*`,
  `<!-- byjohnmichael* -->`). Config, docs and test fixtures don't get one.
