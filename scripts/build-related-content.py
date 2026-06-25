import json
import os
from pathlib import Path

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
SAL = os.path.join(ROOT, "semantic-salience.json")


def load():
    with open(SAL, "r", encoding="utf-8") as f:
        return json.load(f)


def clean(url):
    return url.replace("https://unboundhealing.org", "").rstrip("/")


def build_related_html(related_urls):
    if not related_urls:
        return """
<section class="related-content">
  <h2>Related</h2>
  <p class="muted">No related content found.</p>
</section>
"""

    items = "\n".join(
        f'<a class="chip" href="{clean(u)}">{clean(u).strip("/") or "/"}</a>'
        for u in related_urls
    )

    return f"""
<section class="related-content">
  <h2>Related</h2>
  <div class="chip-cloud">
    {items}
  </div>
</section>
"""


def inject(html, block):
    return html.replace(
        '<div id="related-content"></div>',
        block
    )


def main():
    data = load()
    graph = data.get("page_graph", {})

    pages = Path(ROOT).rglob("*.html")

    updated = 0

    for path in pages:
        html = path.read_text(encoding="utf-8")

        # derive URL key from file path
        rel = "/" + str(path.relative_to(ROOT)).replace("index.html", "").replace(".html", "").strip("/")
        if not rel.startswith("/"):
            rel = "/" + rel

        node = graph.get("https://unboundhealing.org" + rel)

        if not node:
            continue

        related = node.get("related", [])

        block = build_related_html(related)

        if '<div id="related-content"></div>' in html:
            new_html = inject(html, block)
            path.write_text(new_html, encoding="utf-8")
            updated += 1

    print("🔗 RELATED CONTENT COMPLETE")
    print("PAGES UPDATED:", updated)


if __name__ == "__main__":
    main()
