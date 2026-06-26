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
# DISPLAY TITLE (TRUTH-CONSUMER SAFE)
# =========================================================

def get_display_title(node):
    if not isinstance(node, dict):
        return ""

    title = node.get("title")

    if isinstance(title, str) and title.strip():
        return title.strip()

    url = node.get("url", "")
    return url.rstrip("/").split("/")[-1]


# =========================================================
# CENTRALIZED HTML PARSER
# =========================================================

def get_soup(html: str) -> BeautifulSoup:
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
# RELATED BLOCK RENDERER
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
        f'    <a class="semantic-chip" href="{n.get("url", "#")}">{get_display_title(n)}</a>'
        for n in related_nodes
        if isinstance(n, dict)
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
# PLACEHOLDER REPLACEMENT (FIX 2 APPLIED PROPERLY)
# =========================================================

def replace_placeholder(html, block):
    try:
        soup = get_soup(html)

        placeholder = soup.select_one("div.related-content")

        if placeholder is None:
            return html, False

        # -----------------------------
        # FIX 2: SAFE NODE EXTRACTION
        # -----------------------------

        replacement_soup = BeautifulSoup(block, "html.parser")

        replacement_node = replacement_soup.find()

        if replacement_node is None:
            return html, False

        placeholder.replace_with(replacement_node)

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

        related_urls = node.get("related", [])

        related_nodes = [
            n for u in related_urls
            if (n := graph.get(u)) and isinstance(n, dict) and "url" in n
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
