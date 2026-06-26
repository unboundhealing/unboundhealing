#!/usr/bin/env python3

import json
import os
from pathlib import Path
from bs4 import BeautifulSoup

# =========================================================
# ROOT / TRUTH SOURCE
# =========================================================

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))
SAL = ROOT / "semantic-salience.json"


# =========================================================
# LOAD TRUTH
# =========================================================

def load_json():
    with open(SAL, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# CENTRALIZED HTML PARSER (OPTION B HARDENING)
# =========================================================

def get_soup(html: str) -> BeautifulSoup:
    """
    Single enforced HTML parser for the entire pipeline.

    IMPORTANT:
    - prevents accidental reintroduction of lxml
    - guarantees deterministic parsing across CI environments
    """
    return BeautifulSoup(html, "html.parser")


# =========================================================
# CANONICAL URL BUILDER
# =========================================================

def file_to_url(path: Path) -> str:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")

    if rel.endswith("index.html"):
        rel = rel[:-10]
    elif rel.endswith(".html"):
        rel = rel[:-5]

    rel = rel.strip("/")

    if rel:
        return f"https://unboundhealing.org/{rel}/"

    return "https://unboundhealing.org/"


# =========================================================
# HUMAN LABELS
# =========================================================

def url_to_label(url: str) -> str:
    path = (
        url.replace("https://unboundhealing.org", "")
        .strip("/")
    )

    if not path:
        return "Home"

    title = path.split("/")[-1]

    return title.replace("-", " ").title()


# =========================================================
# RELATED BLOCK RENDERER
# =========================================================

def render_block(related_urls):
    if not related_urls:
        return """
<section class="related-content">
  <h3 class="related-paths">Further paths to follow…</h3>
  <p class="muted">No related content available.</p>
</section>
""".strip()

    links = [
        f'    <a class="chip" href="{url}">{url_to_label(url)}</a>'
        for url in related_urls
    ]

    return f"""
<section class="related-content">
  <h3>Further paths to follow…</h3>
  <div class="chip-cloud">
{chr(10).join(links)}
  </div>
</section>
""".strip()


# =========================================================
# PLACEHOLDER REPLACEMENT
# =========================================================

def replace_placeholder(html, block):
    try:
        soup = get_soup(html)

        placeholder = soup.find("div", class_="related-content")

        if placeholder is None:
            return html, False

        replacement = get_soup(block)

        placeholder.replace_with(replacement)

        return str(soup), True

    except Exception as e:
        print("⚠️ replacement error:", e)
        return html, False


# =========================================================
# MAIN
# =========================================================

def main():
    data = load_json()

    graph = data.get("page_graph", {})

    updated = 0

    html_files = [
        p for p in ROOT.rglob("*.html")
        if "assets" not in p.parts
    ]

    for path in html_files:
        url = file_to_url(path)

        node = graph.get(url)

        if node is None:
            print("❌ missing graph node:", url)
            continue

        related = node.get("related", [])

        html = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        block = render_block(related)

        new_html, replaced = replace_placeholder(html, block)

        if not replaced:
            continue

        path.write_text(new_html, encoding="utf-8")

        updated += 1

        print("🔗 injected:", url)

    print()
    print("========================")
    print("RELATED CONTENT COMPLETE")
    print("PAGES UPDATED:", updated)


if __name__ == "__main__":
    main()
