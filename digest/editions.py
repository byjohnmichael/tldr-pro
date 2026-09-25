# All TLDR editions. `slug` is also the path on tldr.tech (https://tldr.tech/{slug}/{date}).
EDITIONS = [
    {"slug": "tech",      "name": "Startups, Tech & Programming", "emoji": None},
    {"slug": "dev",       "name": "Dev",                          "emoji": "💻"},
    {"slug": "ai",        "name": "AI",                           "emoji": "🧠"},
    {"slug": "infosec",   "name": "Information Security",         "emoji": "🔒"},
    {"slug": "product",   "name": "Product Management",           "emoji": "🧑‍🤝‍🧑"},
    {"slug": "devops",    "name": "DevOps",                       "emoji": "☁️"},
    {"slug": "founders",  "name": "Founders",                     "emoji": "👨‍💼"},
    {"slug": "design",    "name": "Design",                       "emoji": "🎨"},
    {"slug": "marketing", "name": "Marketing",                    "emoji": "📈"},
    {"slug": "crypto",    "name": "Crypto",                       "emoji": "🪙"},
    {"slug": "fintech",   "name": "Fintech",                      "emoji": "💰"},
    {"slug": "data",      "name": "Data",                         "emoji": "📊"},
]

ALL_SLUGS = [e["slug"] for e in EDITIONS]

# Section name → content_type classification
# Used to pre-tag articles so user filters work without calling the AI
SECTION_CONTENT_TYPE = {
    "headlines & launches":   "breakthroughs",
    "launches & tools":       "breakthroughs",
    "engineering & research": "breakthroughs",
    "research & innovation":  "breakthroughs",
    "big tech & startups":    "breakthroughs",
    "science & futuristic technology": "breakthroughs",
    "articles & tutorials":   "both",
    "deep dives & analysis":  "both",
    "programming, design & data science": "both",
    "opinions & advice":      "stories",
    "opinions & tutorials":   "stories",
    "miscellaneous":          "stories",
    "quick links":            "stories",
}


def content_type_for_section(section_name: str) -> str:
    """Returns 'breakthroughs', 'stories', or 'both' for a section name."""
    return SECTION_CONTENT_TYPE.get(section_name.lower().strip(), "both")

# byjohnmichael*
