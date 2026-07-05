# TLDR Pro

## The Problem

[TLDR](https://tldr.tech) is a popular daily tech newsletter — but it's actually a family of newsletters. There's one for AI, one for Programming, one for DevOps, one for Marketing, Crypto, and more. If you want to stay broadly informed across tech, you end up subscribed to many of them.

The problem: every morning you're hit with 5-10 long emails. Each one has maybe 2-3 articles you actually care about buried in 10-15 total. You either spend too much time reading all of them, or you stop reading and miss things that matter to you.

## The Solution

TLDR Pro is a locally-run Python tool that runs every morning, collects all of your TLDR newsletters, and uses AI to compile them into **one personalized master digest** — delivered to your inbox by 11 AM.

Instead of reading 8 newsletters, you read one. Instead of every article, you get the ones that are actually relevant to you. The AI learns your preferences over time through simple feedback buttons embedded in the email itself.

## How It Works

```
Every morning at 11 AM
        │
        ▼
1. Connect to your email (IMAP)
   └─ Grabs all TLDR emails received in the last 24 hours
        │
        ▼
2. Parse each newsletter
   └─ Extracts every article: title, blurb, link, section, edition
   └─ Decodes TLDR's tracking URLs to get canonical links
        │
        ▼
3. Merge & deduplicate
   └─ Combines all editions into one pool of articles
   └─ Removes duplicates (same story covered in multiple editions)
        │
        ▼
4. AI-powered selection
   └─ Scores and ranks articles based on your preferences
   └─ Picks the best ~10-12 stories
   └─ Groups them into clean sections
        │
        ▼
5. Send your Master TLDR
   └─ One clean email: intro, sections, blurbs, links
   └─ Feedback buttons ("Not interested", "More like this")
        │
        ▼
6. Learn & improve
   └─ Feedback updates your preference profile
   └─ Next digest is smarter
```

## Current Status

| Module | Status | Description |
|---|---|---|
| `settings.py` | Done | Loads config from `.env`, handles setup wizard |
| `mail.py` | Done | IMAP login, email search/fetch, SMTP send, delete |
| `main.py` | In Progress | Orchestrator — wired up through step 2 |
| `parse_tldr.py` | Planned | Parse HTML newsletters into structured JSON |
| `merge.py` | Planned | Deduplicate and score articles by preference weights |
| `render.py` | Planned | Build the final HTML digest email |
| AI integration | Planned | Claude/OpenAI for intelligent article selection |
| Feedback loop | Planned | Buttons in email that update preference profile |

## Setup

**1. Clone and install dependencies**
```bash
git clone https://github.com/byjohnmichael/tldr-pro
cd tldr-pro
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure your environment**

On first run, TLDR Pro will walk you through a setup wizard that creates your `.env` file. Or copy `.env.example` and fill it in manually:

```env
# Your email login
EMAIL=you@icloud.com
APP_PASSWORD=xxxx-xxxx-xxxx-xxxx   # App-specific password (not your main password)
FOLDER=TLDR                         # Mail folder where TLDR emails land

# Where to send the digest
FROM_ALIAS=tldr@you.com
TO_ALIAS=you@gmail.com

# IMAP/SMTP (iCloud defaults shown)
IMAP_HOST=imap.mail.me.com
IMAP_PORT=993
SMTP_HOST=smtp.mail.me.com
SMTP_PORT=587
```

> **Tip for iCloud users:** Create a mail rule that moves anything addressed to a `tldr@` alias into a dedicated `TLDR` folder. This keeps your main inbox clean and makes the search fast.

**3. Run it**
```bash
python src/main.py
```

## Architecture Notes

- **No external database** — preferences and run logs are stored as simple JSON files locally.
- **Archive by default** — original TLDR emails are archived, not deleted, after a successful send.
- **Rule-based first, AI-enhanced** — the initial scorer uses configurable edition weights. AI selection is layered on top once the pipeline is working.
- **Self-contained** — runs locally via cron or a scheduler. No server required.

## Edition Preference Weights (default)

These control how much the AI favors articles from each TLDR edition. You can tune these in your `.env`.

| Edition | Default Weight |
|---|---|
| Tech | 0.9 |
| Programming | 0.9 |
| AI | 0.9 |
| Design | 0.7 |
| DevOps | 0.3 |
| Business | 0.3 |
| Marketing | 0.2 |

---

Built by [John Michael](https://byjohnmichael.com)
