from typing import List, Dict
from datetime import date
from html import escape

from digest.editions import EDITIONS

# Edition slug → display name lookup
EDITION_NAMES = {e["slug"]: e["name"] for e in EDITIONS}
EDITION_EMOJIS = {e["slug"]: (e["emoji"] or "") for e in EDITIONS}


def render_digest(
    articles: List[Dict],
    intro: str,
    issue_date: str,
) -> tuple[str, str]:
    """
    Builds the HTML digest email.

    Returns:
        (subject, html_body)
    """
    today = date.fromisoformat(issue_date).strftime("%B %d, %Y")
    subject = f"Your TLDR Pro Digest — {today}"

    # Group articles by section for display
    sections: Dict[str, List[Dict]] = {}
    for article in articles:
        section = article["section"]
        sections.setdefault(section, []).append(article)

    # Build article HTML blocks
    sections_html = ""
    for section_name, section_articles in sections.items():
        articles_html = ""
        for article in section_articles:
            edition_label = EDITION_NAMES.get(article["edition"], article["edition"].upper())
            edition_emoji = EDITION_EMOJIS.get(article["edition"], "")

            read_time = ""
            if article.get("minutes_read"):
                read_time = f'<span style="color:#888;font-size:12px;"> · {article["minutes_read"]} min read</span>'

            blurb_html = ""
            if article.get("blurb"):
                blurb_html = f'<p style="margin:6px 0 0 0;color:#444;font-size:14px;line-height:1.5;">{escape(article["blurb"])}</p>'

            articles_html += f"""
            <div style="margin-bottom:24px;">
              <p style="margin:0 0 2px 0;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">
                {edition_emoji} {edition_label}
              </p>
              <a href="{escape(article['canonical_url'])}"
                 style="font-size:16px;font-weight:600;color:#1a1a1a;text-decoration:none;line-height:1.3;">
                {escape(article['title'])}
              </a>{read_time}
              {blurb_html}
            </div>"""

        sections_html += f"""
        <tr>
          <td style="padding:8px 0 4px 0;">
            <h2 style="margin:0;font-size:13px;font-weight:700;text-transform:uppercase;
                       letter-spacing:1px;color:#555;border-bottom:1px solid #eee;padding-bottom:8px;">
              {escape(section_name)}
            </h2>
          </td>
        </tr>
        <tr>
          <td style="padding:12px 0 24px 0;">
            {articles_html}
          </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#fff;border-radius:8px;overflow:hidden;max-width:600px;width:100%;">

          <!-- Header -->
          <tr>
            <td style="background:#1a1a1a;padding:24px 32px;text-align:center;">
              <span style="font-size:28px;font-weight:800;letter-spacing:-1px;">
                <span style="color:#4ea8f5;">T</span><span style="color:#e4b44e;">L</span><span style="color:#56b89d;">D</span><span style="color:#d15458;">R</span>
                <span style="color:#fff;font-weight:400;font-size:20px;"> Pro</span>
              </span>
              <p style="margin:8px 0 0 0;color:#aaa;font-size:13px;">{today}</p>
            </td>
          </tr>

          <!-- Intro -->
          <tr>
            <td style="padding:24px 32px 16px 32px;border-bottom:1px solid #f0f0f0;">
              <p style="margin:0;font-size:15px;color:#333;line-height:1.6;font-style:italic;">
                {escape(intro)}
              </p>
            </td>
          </tr>

          <!-- Articles -->
          <tr>
            <td style="padding:0 32px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                {sections_html}
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 32px;border-top:1px solid #f0f0f0;text-align:center;">
              <p style="margin:0;font-size:12px;color:#aaa;">
                Curated from <a href="https://tldr.tech" style="color:#aaa;">tldr.tech</a>.
                Edit config.yaml to change what you get.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return subject, html
