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
# DISPLAY TITLE
# =========================================================

def get_display_title(node):
    if not node:
        return ""

    title = node.get("title")

    if isinstance(title, str) and title.strip():
        return title.strip()

    url = node.get("url", "")
    return url.rstrip("/").split("/")[-1]

# =========================================================
# CENTRALIZED HTML PARSER (OPTION B HARDENING)
# =========================================================

def get_soup(html: str) -> BeautifulSoup:
    """
    Single enforced HTML parser for the entire pipeline.
    Prevents parser drift across CI/runtime environments.
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
# RELATED BLOCK RENDERER (NODE-AWARE, TRUTH-ALIGNED)
# =========================================================

def render_block(related_nodes):

    if not related_nodes:
        return """
<section class="semantic-block related-paths">

  <h3>Further paths to follow...</h3>

  <div class="semantic-cloud">
    <span class="semantic-chip muted">No related content available.</span>
  </div>

</section>
""".strip()

    links = "\n".join(
        f'    <a class="semantic-chip" href="{n["url"]}">{get_display_title(n)}</a>'
        for n in related_nodes[:3]
    )

    return f"""
<section class="semantic-block related-paths">

  <h3>Further paths to follow...</h3>

  <div class="semantic-cloud">
{links}
  </div>

</section>
""".strip()


# =========================================================
# PLACEHOLDER REPLACEMENT
# =========================================================

def replace_placeholder(html, block):
    try:
        soup = get_soup(html)

        placeholder = soup.select_one("div.related-content")

        if placeholder is None:
            return html, False

        replacement = BeautifulSoup(block, "html.parser").contents[0]

        placeholder.replace_with(replacement.contents[0])

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

        # convert URL list → node list (TRUTH ALIGNED)
        related_urls = node.get("related", [])

        related_nodes = [
            graph.get(u)
            for u in related_urls
            if graph.get(u) is not None
        ]

        html = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        block = render_block(related_nodes)

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
