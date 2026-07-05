from typing import Optional

# All TLDR editions with their metadata
EDITIONS = [
    {"slug": "tech",      "name": "Startups, Tech & Programming", "emoji": None,  "from_name": "TLDR"},
    {"slug": "dev",       "name": "Dev",                          "emoji": "💻",  "from_name": "TLDR Dev"},
    {"slug": "ai",        "name": "AI",                           "emoji": "🧠",  "from_name": "TLDR AI"},
    {"slug": "infosec",   "name": "Information Security",         "emoji": "🔒",  "from_name": "TLDR Information Security"},
    {"slug": "product",   "name": "Product Management",           "emoji": "🧑‍🤝‍🧑", "from_name": "TLDR Product Management"},
    {"slug": "devops",    "name": "DevOps",                       "emoji": "☁️",  "from_name": "TLDR DevOps"},
    {"slug": "founders",  "name": "Founders",                     "emoji": "👨‍💼",  "from_name": "TLDR Founders"},
    {"slug": "design",    "name": "Design",                       "emoji": "🎨",  "from_name": "TLDR Design"},
    {"slug": "marketing", "name": "Marketing",                    "emoji": "📈",  "from_name": "TLDR Marketing"},
    {"slug": "crypto",    "name": "Crypto",                       "emoji": "🪙",  "from_name": "TLDR Crypto"},
    {"slug": "fintech",   "name": "Fintech",                      "emoji": "💰",  "from_name": "TLDR Fintech"},
    {"slug": "data",      "name": "Data",                         "emoji": "📊",  "from_name": "TLDR Data"},
]

# Maps the "from_name" (as it appears in the From: header) to a slug
_FROM_NAME_TO_SLUG = {e["from_name"].lower(): e["slug"] for e in EDITIONS}

# Section name → content_type classification
# Used to pre-tag articles so user filters work without calling the AI
SECTION_CONTENT_TYPE = {
    "headlines & launches":   "breakthroughs",
    "launches & tools":       "breakthroughs",
    "engineering & research": "breakthroughs",
    "articles & tutorials":   "both",
    "deep dives & analysis":  "both",
    "opinions & advice":      "stories",
    "miscellaneous":          "stories",
    "quick links":            "stories",
}


def slug_from_from_header(from_header: str) -> Optional[str]:
    """
    Parses the From: header (e.g. 'TLDR AI <dan@tldrnewsletter.com>')
    and returns the edition slug (e.g. 'ai'), or None if unrecognized.
    """
    # Extract display name before the email address
    name_part = from_header.split("<")[0].strip().strip('"').lower()
    # Direct match
    if name_part in _FROM_NAME_TO_SLUG:
        return _FROM_NAME_TO_SLUG[name_part]
    # Partial match (handles edge cases)
    for from_name, slug in _FROM_NAME_TO_SLUG.items():
        if from_name in name_part or name_part in from_name:
            return slug
    return None


def content_type_for_section(section_name: str) -> str:
    """Returns 'breakthroughs', 'stories', or 'both' for a section name."""
    return SECTION_CONTENT_TYPE.get(section_name.lower().strip(), "both")
