# TLDR Pro

[TLDR](https://tldr.tech) is a family of a dozen daily newsletters. Each has a few stories you
care about buried among ones you don't. TLDR Pro reads all of today's issues and sends you
**one** personalized digest with the articles an AI picked for you.

## How it works

```
GitHub Actions, every morning (14:00 UTC)
  1. Fetch   today's issues from https://tldr.tech/{edition}/{date}
  2. Curate  Claude Haiku picks N articles using config.yaml
  3. Render  one clean HTML email, grouped by section
  4. Send    via iCloud SMTP
```

No inbox access, no database, no server. If something breaks, the Action fails and GitHub emails you.

## Setup

1. Add repository secrets: `ANTHROPIC_API_KEY`, `ICLOUD_EMAIL`, `ICLOUD_APP_PASSWORD`
   (an app-specific password).
2. Edit `config.yaml` with your email and preferences.
3. Actions → **Daily digest** → **Run workflow**, with *dry run* checked the first time. The
   rendered email is attached to the run as the `digest` artifact.

## Local run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m digest.main --dry-run   # writes out/digest.html
pytest -q tests
```

---

Built by [John Michael](https://byjohnmichael.com)
