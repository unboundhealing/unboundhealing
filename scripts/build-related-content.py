import json
import os
from pathlib import Path

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SAL = os.path.join(ROOT, "semantic-salience.json")


# -----------------------------
# LOAD TRUTH LAYER
# -----------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# NORMALIZE URL MATCHING
# -----------------------------
def normalize(url):
    return url.replace("https://unboundhealing.org", "").strip("/") or "/"


# -----------------------------
# BUILD RELATED BLOCK
# -----------------------------
def render_related(page_url, page_graph):
    node = page_graph.get(page_url, None)

    if not node:
        return "<section class='related-content'><p class='muted'>No related content.</p></section>"

    related = node.get("related", [])

    if not related:
        return "<section class='related-content'><p class='muted'>No related content.</p></section>"

    chips = []

    for r in related:
        label = r.strip("/").split("/")[-1].replace("-", " ").title()
        href = r
        chips.append(f'<a class="chip" href="{href}">{label}</a>')

    return f"""
<section class="related-content">
  <h2>Related</h2>
  <div class="chip-cloud">
    {''.join(chips)}
  </div>
</section>
""".strip()


# -----------------------------
# INJECT INTO HTML FILE
# -----------------------------
def inject(html, block):
    return html.replace(
        '<div id="related-content"></div>',
        block
    )


# -----------------------------
# MAIN BUILD
# -----------------------------
def main():
    if not os.path.exists(SAL):
        raise FileNotFoundError("semantic-salience.json missing")

    data = load_json(SAL)
    page_graph = data.get("page_graph", {})

    replaced = 0

    for path in Path(ROOT).rglob("*.html"):
        html = path.read_text(encoding="utf-8")

        if '<div id="related-content"></div>' not in html:
            continue

        # derive URL key from file path
        rel_path = "/" + str(path.relative_to(ROOT)).replace("index.html", "").replace(".html", "").strip("/")
        if not rel_path.endswith("/"):
            rel_path += "/"

        block = render_related(rel_path, page_graph)
        new_html = inject(html, block)

        path.write_text(new_html, encoding="utf-8")

        print("🔗 injected related:", path)
        replaced += 1

    print("\n========================")
    print("RELATED CONTENT COMPLETE")
    print("PAGES UPDATED:", replaced)


if __name__ == "__main__":
    main()
