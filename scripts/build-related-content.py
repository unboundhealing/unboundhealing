#!/usr/bin/env python3

import json
import os
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
SAL = os.path.join(ROOT, "semantic-salience.json")


# ---------------------------------------------------------
# LOAD TRUTH
# ---------------------------------------------------------

def load_json():
    with open(SAL, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# SINGLE CANONICAL URL BUILDER
# ---------------------------------------------------------

def file_to_url(path):
    rel = str(path.relative_to(ROOT)).replace("\\", "/")

    if rel.endswith("index.html"):
        rel = rel[:-10]
    elif rel.endswith(".html"):
        rel = rel[:-5]

    rel = rel.strip("/")

    if rel:
        return f"https://unboundhealing.org/{rel}/"

    return "https://unboundhealing.org/"


# ---------------------------------------------------------
# HUMAN LABELS
# ---------------------------------------------------------

def url_to_label(url):
    path = (
        url.replace("https://unboundhealing.org", "")
        .strip("/")
    )

    if not path:
        return "Home"

    title = path.split("/")[-1]

    return title.replace("-", " ").title()


# ---------------------------------------------------------
# RELATED BLOCK RENDERER
# ---------------------------------------------------------

def render_block(related_urls):

    if not related_urls:
        return """
<section class="related-content">
  <h2>Related</h2>
  <p class="muted">No related content available.</p>
</section>
""".strip()

    links = []

    for url in related_urls:
        links.append(
            f'    <a class="chip" href="{url}">{url_to_label(url)}</a>'
        )

    return f"""
<section class="related-content">
  <h2>Related</h2>
  <div class="chip-cloud">
{chr(10).join(links)}
  </div>
</section>
""".strip()


# ---------------------------------------------------------
# PLACEHOLDER REPLACEMENT
# ---------------------------------------------------------

def replace_placeholder(html, block):

    try:
        soup = BeautifulSoup(html, "html.parser")

        placeholder = soup.find(
            "div",
            class_="related-content"
        )

        if placeholder is None:
            return html, False

        replacement = BeautifulSoup(
            block,
            "html.parser"
        )

        placeholder.replace_with(replacement)

        return str(soup), True

    except Exception as e:
        print("⚠️ replacement error:", e)
        return html, False


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    data = load_json()

    graph = data.get("page_graph", {})

    updated = 0

    html_files = [
        p for p in Path(ROOT).rglob("*.html")
        if "/assets/" not in str(p).replace("\\", "/")
    ]

    for path in html_files:

        url = file_to_url(path)

        node = graph.get(url)

        if node is None:
            print("❌ NO NODE MATCH:", url)
            continue

        related = node.get("related", [])

        html = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        block = render_block(related)

        new_html, replaced = replace_placeholder(
            html,
            block
        )

        if not replaced:
            continue

        path.write_text(
            new_html,
            encoding="utf-8"
        )

        updated += 1

        print("🔗 injected:", url)

    print()
    print("========================")
    print("RELATED CONTENT COMPLETE")
    print("PAGES UPDATED:", updated)


if __name__ == "__main__":
    main()
