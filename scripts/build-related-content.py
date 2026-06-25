import json
import os
from pathlib import Path

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
SAL = os.path.join(ROOT, "semantic-salience.json")


# -----------------------------
# LOAD TRUTH
# -----------------------------
def load_json():
    with open(SAL, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# URL NORMALIZATION (ABSOLUTE TRUTH)
# -----------------------------
def normalize(url: str) -> str:
    """
    Forces ALL URLs into canonical form:
    https://unboundhealing.org/path/
    """
    if not url:
        return None

    url = url.replace("https://unboundhealing.org", "")
    url = url.replace("index.html", "")
    url = url.replace(".html", "")

    if not url.startswith("/"):
        url = "/" + url

    if not url.endswith("/"):
        url = url + "/"

    return "https://unboundhealing.org" + url


# -----------------------------
# RENDER RELATED BLOCK
# -----------------------------
def render_block(related_urls):
    if not related_urls:
        return """
<section class="related-content">
  <h2>Related</h2>
  <p class="muted">No related content.</p>
</section>
""".strip()

    chips = []

    for url in related_urls:
        clean = normalize(url)
        if not clean:
            continue

        label = clean.replace("https://unboundhealing.org", "").strip("/").replace("-", " ").title()
        chips.append(f'<a class="chip" href="{clean}">{label}</a>')

    return f"""
<section class="related-content">
  <h2>Related</h2>
  <div class="chip-cloud">
    {''.join(chips)}
  </div>
</section>
""".strip()


# -----------------------------
# INJECTOR
# -----------------------------
def inject(html, block):
    return html.replace(
        "<div id=\"related-content\"></div>",
        block
    )


# -----------------------------
# MAIN
# -----------------------------
def main():
    data = load_json()
    graph = data.get("page_graph", {})

    pages = Path(ROOT).rglob("*.html")

    updated = 0

    for path in pages:
        html = path.read_text(encoding="utf-8")

        if "<div id=\"related-content\"></div>" not in html:
            continue

        # derive page URL from file path
        rel = str(path.relative_to(ROOT))

        url = "https://unboundhealing.org/" + rel
        url = url.replace("index.html", "")
        url = url.replace(".html", "")

        if not url.endswith("/"):
            url += "/"

        node = graph.get(url)

        if not node:
            # fallback: try normalized again just in case
            node = graph.get(normalize(url))

        if not node:
            print("❌ NO NODE MATCH:", url)
            continue

        related = node.get("related", [])

        block = render_block(related)

        new_html = inject(html, block)
        path.write_text(new_html, encoding="utf-8")

        updated += 1
        print("🔗 injected:", url)

    print("\n========================")
    print("RELATED CONTENT COMPLETE")
    print("PAGES UPDATED:", updated)


if __name__ == "__main__":
    main()
