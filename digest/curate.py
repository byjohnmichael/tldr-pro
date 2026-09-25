import json
import subprocess
from typing import List, Dict, Optional

from digest.editions import ALL_SLUGS

# Article counts per digest length setting
DIGEST_LENGTH_MAP = {
    "short":  5,
    "medium": 10,
    "long":   18,
}

# Defaults for any key missing from config.yaml
DEFAULT_PREFERENCES = {
    "editions":             ALL_SLUGS,
    "content_type":         "both",
    "digest_length":        "medium",
    "interest_tags":        [],
    "exclude_topics":       [],
    "custom_instructions":  "",
}


def filter_articles_for_user(articles: List[Dict], preferences: Dict) -> List[Dict]:
    """
    Pre-filters the article pool before sending to the AI.
    Applies edition selection and content_type filter.
    """
    selected_editions = preferences.get("editions") or DEFAULT_PREFERENCES["editions"]
    content_type = preferences.get("content_type", "both")

    filtered = []
    for article in articles:
        # Edition filter
        if article["edition"] not in selected_editions:
            continue

        # Content type filter (section-based pre-tagging)
        section_type = article.get("section_content_type", "both")
        if content_type == "breakthroughs" and section_type == "stories":
            continue
        if content_type == "stories" and section_type == "breakthroughs":
            continue

        filtered.append(article)

    return filtered


def curate_for_user(
    articles: List[Dict],
    preferences: Optional[Dict] = None,
) -> Dict:
    """
    Calls Claude Haiku to select the best articles for a user.

    Returns:
        {
            "selected_ids": ["id1", "id2", ...],
            "intro": "One sentence personalized intro"
        }
    """
    prefs = {**DEFAULT_PREFERENCES, **(preferences or {})}

    filtered = filter_articles_for_user(articles, prefs)
    if not filtered:
        print("  WARNING: No articles after filtering. Using full pool.")
        filtered = articles

    target_count = DIGEST_LENGTH_MAP.get(prefs["digest_length"], 10)

    # Build a compact article list for the prompt (id, edition, section, title, blurb)
    article_pool = [
        {
            "id": a["id"],
            "edition": a["edition"],
            "section": a["section"],
            "title": a["title"],
            "blurb": a["blurb"],
        }
        for a in filtered
    ]

    tags_str = ", ".join(prefs["interest_tags"]) or "none specified"
    exclude_str = ", ".join(prefs["exclude_topics"]) or "none"
    custom_str = prefs["custom_instructions"] or "none"

    content_type_explanation = {
        "breakthroughs": "major launches, releases, and research only — skip opinion pieces and side stories",
        "stories": "opinion pieces, tutorials, and interesting reads — skip major launch announcements",
        "both": "a good mix of launches, research, opinions, and tutorials",
    }.get(prefs["content_type"], "a good mix")

    system_prompt = (
        "You are a newsletter curator. Your job is to select the best articles for a specific user "
        "based on their preferences. Return only valid JSON — no explanation, "
        "no markdown, just the JSON object."
    )

    user_prompt = f"""Select the best {target_count} articles for this user from today's TLDR newsletters.

User preferences:
- Content focus: {content_type_explanation}
- Interest tags (prioritize these topics): {tags_str}
- Exclude topics (avoid these): {exclude_str}
- Custom instructions: {custom_str}

Available articles ({len(article_pool)} total):
{json.dumps(article_pool, indent=2)}

Select exactly {target_count} articles. Prioritize variety across editions and sections.
Return this JSON and nothing else:
{{
  "selected_ids": ["id1", "id2", ...],
  "intro": "One sentence personalized intro for today's digest (conversational tone, no fluff)"
}}"""

    raw = ask_claude(system_prompt, user_prompt)
    result = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])

    # Validate structure
    if "selected_ids" not in result or "intro" not in result:
        raise ValueError(f"Unexpected response shape from Haiku: {raw}")

    # Drop any IDs the model invented, then cap to target_count
    valid_ids = {a["id"] for a in filtered}
    result["selected_ids"] = [i for i in result["selected_ids"] if i in valid_ids][:target_count]

    return result


def ask_claude(system_prompt: str, user_prompt: str) -> str:
    """
    Runs Claude Code headless on your Claude plan (no API key). Auth comes from
    CLAUDE_CODE_OAUTH_TOKEN (create with `claude setup-token`) or your local login.
    """
    proc = subprocess.run(
        ["claude", "-p", "--model", "haiku", "--output-format", "json",
         "--tools", "", "--system-prompt", system_prompt],
        input=user_prompt, capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {proc.stderr.strip() or proc.stdout.strip()}")
    response = json.loads(proc.stdout)
    if response.get("is_error"):
        raise RuntimeError(f"claude CLI error: {response.get('result')}")
    return response["result"]
