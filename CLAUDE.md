# TLDR Pro — Claude Context

## What This Project Is

An AI-powered newsletter personalization platform. John Michael receives all 12 TLDR
newsletter editions to his iCloud inbox every morning. Because TLDR sends the same content
to everyone, his inbox is the shared source of truth. The pipeline fetches and parses
those emails once, then uses Claude Haiku to curate a personalized digest for each user.
Users never connect their email — they just sign up with an address to receive the digest.

---

## Architecture

```
tldr-pro/
├── pipeline/          # Daily digest pipeline (runs via GitHub Actions cron)
│   ├── main.py        # Orchestrator — entry point (python -m pipeline.main)
│   ├── fetch.py       # iCloud IMAP fetch + trash (MailClient, fetch_tldr_emails, trash_fetched_emails)
│   ├── parse.py       # BeautifulSoup HTML → article dicts
│   ├── curate.py      # Claude Haiku article selection per user
│   ├── render.py      # HTML digest email builder
│   └── send.py        # iCloud SMTP email delivery
├── shared/
│   ├── editions.py    # Edition metadata + section→content_type mapping
│   └── db.py          # (Phase 2) Supabase client
├── tests/
│   ├── run_ai_short.py  # End-to-end test: AI edition, short digest, both types
│   └── output/          # Rendered HTML output from test runs (gitignored)
├── api/               # (Phase 4) FastAPI backend for Vercel
├── web/               # (Phase 4) React frontend for Vercel
├── src/               # LEGACY — superseded by pipeline/ and shared/
├── .env               # Secrets (gitignored)
├── .env.example       # Template
└── requirements.txt
```

---

## Stack
- **Pipeline:** Python 3.12+, BeautifulSoup4, anthropic SDK
- **AI:** Claude Haiku (`claude-haiku-4-5-20251001`) — cheapest, fast, ~$0.005/user/day
- **Email send:** iCloud SMTP (`smtp.mail.me.com:587`, STARTTLS) — sends from `tldr@byjohnmichael.com`
- **Email fetch:** iCloud IMAP (`imap.mail.me.com:993`) via Python stdlib `imaplib`
- **Database:** Supabase / Postgres (Phase 2+)
- **Frontend:** React + TypeScript on Vercel (Phase 4)
- **Backend API:** FastAPI on Vercel (Phase 4)
- **Scheduler:** GitHub Actions cron `0 14 * * *` (6 AM PST / 7 AM PDT)

---

## Running the Pipeline

```bash
# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set up env (copy .env.example → .env and fill in values)
cp .env.example .env

# Run production pipeline (fetches, curates, sends, then trashes source emails)
python -m pipeline.main

# Run test (AI edition only, short digest, emails NOT trashed)
python tests/run_ai_short.py
```

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `ICLOUD_EMAIL` | John's iCloud login email (used for both IMAP fetch and SMTP send) |
| `ICLOUD_APP_PASSWORD` | App-specific password (not Apple ID password) |
| `ICLOUD_IMAP_HOST` | `imap.mail.me.com` |
| `ICLOUD_IMAP_PORT` | `993` |
| `ICLOUD_FOLDER` | `TLDR` (mail rule routes all TLDR newsletters here) |
| `TO_EMAIL` | Where to send the digest (Phase 1: `jm@byjohnmichael.com`) |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `FROM_EMAIL` | `tldr@byjohnmichael.com` |

Note: `RESEND_API_KEY` is no longer used — send.py was switched to iCloud SMTP.

---

## TLDR Editions (12 total)

| Slug | Name | From name in email |
|---|---|---|
| `tech` | Startups, Tech & Programming | TLDR |
| `dev` | Dev | TLDR Dev |
| `ai` | AI | TLDR AI |
| `infosec` | Information Security | TLDR Information Security |
| `product` | Product Management | TLDR Product Management |
| `devops` | DevOps | TLDR DevOps |
| `founders` | Founders | TLDR Founders |
| `design` | Design | TLDR Design |
| `marketing` | Marketing | TLDR Marketing |
| `crypto` | Crypto | TLDR Crypto |
| `fintech` | Fintech | TLDR Fintech |
| `data` | Data | TLDR Data |

Not all editions publish daily — the 24-hour fetch window handles this automatically.

---

## User Preferences (6 inputs)

1. `editions` — list of edition slugs to pull from
2. `content_type` — `"breakthroughs"` | `"stories"` | `"both"`
3. `digest_length` — `"short"` (5) | `"medium"` (10) | `"long"` (18)
4. `interest_tags` — list of topic strings, e.g. `["LLMs", "open source"]`
5. `exclude_topics` — blocklist of topic strings
6. `custom_instructions` — free text passed verbatim into the Claude Haiku prompt

---

## Email HTML Parsing Notes

TLDR emails are heavily nested HTML tables. Key parser details in `pipeline/parse.py`:

- **Edition detection:** From the `From:` header display name (e.g. `TLDR AI`)
- **Section headers:** `<h1><strong>Section Name</strong></h1>` inside a `<td>` with no links
- **Article structure:** Each article is a `<div class="text-block"><span><a>Title</a><br><br><span>Blurb</span></span></div>`
- **Blurb extraction:** Sibling `<span>` after the `<a>` tag (NOT a sibling of the `<td>`)
- **Tracking URLs:** Format `https://tracking.tldrnewsletter.com/CL0/https:%2F%2Factual.com/...`
  — URL-decode the segment after `/CL0/` to get the canonical URL
- **Sponsor detection:** Title text contains `(Sponsor)` — these are skipped
- **Read time:** Regex `\(\d+ minute read\)` in the title text
- **Section→content_type mapping:** In `shared/editions.py → SECTION_CONTENT_TYPE`

---

## Pipeline Article Schema

```python
{
    "id":                   "ai-2026-02-20-headlines-launches-001",
    "edition":              "ai",
    "issue_date":           "2026-02-20",
    "section":              "Headlines & Launches",
    "section_content_type": "breakthroughs",   # "breakthroughs" | "stories" | "both"
    "title":                "Article title",
    "blurb":                "One or two sentence summary.",
    "canonical_url":        "https://actual-url.com/path",
    "minutes_read":         5,                 # None for GitHub repos
    "is_sponsor":           False,
}
```

---

## Pipeline Flow

1. **Fetch** (`fetch.py`) — Connect to iCloud IMAP, search `TLDR` folder for emails from
   `@tldrnewsletter.com` in past 24h. Returns `(emails, uids)` — both HTML content and
   IMAP UIDs. UIDs are held until all users are processed, then used to trash the source emails.

2. **Parse** (`parse.py`) — Walk all `<td>` cells. Detect section headers and article blocks.
   Extract title, blurb, canonical URL, read time. Skip sponsors. Deduplicate by canonical URL.
   Returns flat list of article dicts.

3. **Curate** (`curate.py`) — Filter articles by user's edition + content_type preferences.
   Send pool to Claude Haiku which selects N articles and writes a personalized intro.
   Returns `{"selected_ids": [...], "intro": "..."}`.

4. **Render** (`render.py`) — Build HTML email grouped by section. Articles include title,
   edition label, read time, blurb, and 👍/👎 feedback links (point to future Phase 4 API).

5. **Send** (`send.py`) — Deliver via iCloud SMTP from `tldr@byjohnmichael.com`.

6. **Trash** (`fetch.py → trash_fetched_emails()`) — Mark source emails as `\Deleted` and
   expunge. iCloud moves them to "Deleted Messages". Only called after all users are sent.
   Skipped when `trash=False` (test mode).

---

## Test Script

`tests/run_ai_short.py` runs the full pipeline end-to-end with fixed preferences:
- Editions: `["ai"]`
- Content type: `"both"`
- Digest length: `"short"` (5 articles)
- Sends to `TO_EMAIL` from `.env`
- Saves rendered HTML to `tests/output/ai_short_latest.html`
- `TRASH_AFTER_SEND = False` at top of file — flip to `True` for a full clean run

Run from project root: `python tests/run_ai_short.py`

---

## Implementation Phases

| Phase | Status | Description |
|---|---|---|
| 1 — Core Pipeline | **Complete** | Fetch → Parse → Curate → Render → Send → Trash (single user) |
| 2 — Database | **Next** | Supabase schema, store articles + digests, load prefs from DB |
| 3 — Multi-user | Planned | Loop over users from DB, feedback endpoint |
| 4 — Web App | Planned | FastAPI + React, signup, onboarding, profile page |
| 5 — Polish | Planned | GitHub Actions cron, error handling, launch |

---

## Known Issues / Open Items

- **Section detection** — needs verification that articles are grouped under correct sections
  (e.g. "Headlines & Launches") rather than falling back to "General". Test and confirm
  with a live run.
- **Feedback links** — 👍/👎 URLs in the rendered email point to `https://api.tldrpro.com`
  which doesn't exist until Phase 4. Dead links for now.
- **iCloud SMTP from address** — SMTP login uses `ICLOUD_EMAIL` but `From` header is
  `tldr@byjohnmichael.com`. iCloud may rewrite this. Verify from field in delivered email.

---

## Conventions

- Python 3.12+
- `python-dotenv` for env loading (`load_dotenv()` called in `pipeline/main.py`)
- All modules importable as `pipeline.x` or `shared.x` — run from project root
- No database in Phase 1 — preferences hardcoded in `pipeline/main.py` `PHASE1_USER`
- Sponsors are always skipped by the parser (never reach the AI)
- `main.run(trash=True)` — pass `trash=False` to skip trashing source emails
