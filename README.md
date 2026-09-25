# TLDR Pro

[TLDR](https://tldr.tech) publishes a dozen daily newsletters (Tech, AI, Dev, Design, InfoSec,
Product, and more). Subscribing to all of them means wading through a dozen emails a day, each
with a few stories you care about buried among ones you don't.

TLDR Pro reads all of the day's issues for you and sends you **one** email with just the articles
worth your time. An AI picks them based on the editions, topics and length you set in
`config.yaml`.

## How it works

```
Every morning (14:00 UTC, 6 AM PST / 7 AM PDT)
  1. Fetch   today's issues from https://tldr.tech/{edition}/{date}
  2. Curate  Claude Haiku (via Claude Code on a Claude plan) picks the articles that match config.yaml
  3. Render  one clean HTML email, grouped by section
  4. Send    via iCloud SMTP
```

It has no inbox access, no database and no server. Each run stands on its own. On days TLDR
doesn't publish (weekends, holidays), nothing is sent. If something breaks, the run fails and
GitHub emails you.

## Where it runs

**Today:** GitHub Actions only (`.github/workflows/daily.yml`). The workflow runs the digest on a
daily schedule, and you can also start it by hand with an optional date and a dry-run toggle.

**Next:**
- **Run locally.** Run it on a schedule on your own machine instead of relying on GitHub Actions.
  You can already run it by hand (see [Local run](#local-run)).
- **Run as a service.** Host it so it runs without a GitHub repo or a personal machine.

The pipeline in `digest/` doesn't depend on GitHub Actions. The workflow only runs
`python -m digest.main`, and everything else comes from environment variables and `config.yaml`.
So moving it somewhere else only means changing what runs it.

## Setup (GitHub Actions)

1. Add these repository secrets (Settings → Secrets and variables → Actions → *Repository secrets*):
   - `CLAUDE_CODE_OAUTH_TOKEN`: run `claude setup-token` on your computer and paste the result.
   - `ICLOUD_EMAIL`: your Apple ID / `@icloud.com` address. Use this even if the digest is sent
     from a custom-domain address, because iCloud rejects custom-domain aliases as a login.
   - `ICLOUD_APP_PASSWORD`: an app-specific password from account.apple.com.
2. Edit `config.yaml` with your address and preferences.
3. Go to Actions → **Daily digest** → **Run workflow**, and check *dry run* the first time. The
   rendered email is attached to the run as the `digest` artifact.

## Preferences

All set in `config.yaml`:

| Setting | What it does |
|---|---|
| `editions` | Which TLDR newsletters to read |
| `content_type` | `breakthroughs`, `stories`, or `both` |
| `digest_length` | `short` (5), `medium` (10), or `long` (18) articles |
| `interest_tags` | Topics to favor, e.g. `[LLMs, open source, Rust]` |
| `exclude_topics` | Topics to skip |
| `custom_instructions` | Free text passed straight to the curator |

## Local run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # fill in the same values as the secrets above
python -m digest.main --dry-run   # writes out/digest.html without sending
python -m digest.main             # sends
pytest -q tests
```

Locally, curation uses your logged-in Claude Code, so `CLAUDE_CODE_OAUTH_TOKEN` is optional.

---

Built by [John Michael](https://byjohnmichael.com)
