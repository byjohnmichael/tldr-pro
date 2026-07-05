import json
import os
from typing import List, Dict, Optional
import anthropic

# Article counts per digest length setting
DIGEST_LENGTH_MAP = {
    "short":  5,
    "medium": 10,
    "long":   18,
}

# Default preferences used when running for a single user (Phase 1 / local testing)
DEFAULT_PREFERENCES = {
    "editions":             ["tech", "dev", "ai", "infosec", "product", "devops",
                             "founders", "design", "marketing", "crypto", "fintech", "data"],
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


def build_feedback_summary(feedback: List[Dict]) -> Dict[str, List[str]]:
    """
    Summarizes recent feedback into liked/disliked title lists for the AI prompt.
    feedback items: {"article_title": str, "action": "more_like_this" | "not_interested"}
    """
    liked = [f["article_title"] for f in feedback if f.get("action") == "more_like_this"]
    disliked = [f["article_title"] for f in feedback if f.get("action") == "not_interested"]
    return {"liked": liked[:10], "disliked": disliked[:10]}  # cap to keep prompt lean


def curate_for_user(
    articles: List[Dict],
    preferences: Optional[Dict] = None,
    feedback: Optional[List[Dict]] = None,
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
    feedback = feedback or []

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

    feedback_summary = build_feedback_summary(feedback)
    liked_str = ", ".join(f'"{t}"' for t in feedback_summary["liked"]) or "none yet"
    disliked_str = ", ".join(f'"{t}"' for t in feedback_summary["disliked"]) or "none yet"

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
        "based on their preferences and feedback history. Return only valid JSON — no explanation, "
        "no markdown, just the JSON object."
    )

    user_prompt = f"""Select the best {target_count} articles for this user from today's TLDR newsletters.

User preferences:
- Content focus: {content_type_explanation}
- Interest tags (prioritize these topics): {tags_str}
- Exclude topics (avoid these): {exclude_str}
- Custom instructions: {custom_str}
- Feedback — previously liked: {liked_str}
- Feedback — previously disliked: {disliked_str}

Available articles ({len(article_pool)} total):
{json.dumps(article_pool, indent=2)}

Select exactly {target_count} articles. Prioritize variety across editions and sections.
Return this JSON and nothing else:
{{
  "selected_ids": ["id1", "id2", ...],
  "intro": "One sentence personalized intro for today's digest (conversational tone, no fluff)"
}}"""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": user_prompt}],
        system=system_prompt,
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if the model adds them despite instructions
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    result = json.loads(raw)

    # Validate structure
    if "selected_ids" not in result or "intro" not in result:
        raise ValueError(f"Unexpected response shape from Haiku: {raw}")

    # Cap to target_count in case the model returns more
    result["selected_ids"] = result["selected_ids"][:target_count]

    return result
