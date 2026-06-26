#!/usr/bin/env python3

import json
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse

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

def normalize_url(url: str) -> str:
    if not isinstance(url, str):
        return ""

    url = url.strip()

    if not url:
        return ""

    # remove domain if present
    if url.startswith("http"):
        url = urlparse(url).path

    # ensure leading slash
    if not url.startswith("/"):
        url = "/" + url

    # collapse duplicate slashes
    url = re.sub(r"/+", "/", url)

    # enforce trailing slash
    if not url.endswith("/"):
        url += "/"

    return url

# =========================================================
# RELATED BLOCK RENDERER
# =========================================================

def render_block_with_graph(related_nodes, graph, current_url):

    # =========================================================
    # CURRENT PAGE CONTEXT (CRITICAL FIX)
    # This anchors fallback logic properly
    # =========================================================

    current_node = graph.get(current_url)

    seed = set()
    if isinstance(current_node, dict):
        seed |= set(current_node.get("concepts", []))

    # also include related node concepts (secondary signal)
    for n in related_nodes:
        if isinstance(n, dict):
            seed |= set(n.get("concepts", []))

    # =========================================================
    # TIER 0 — DIRECT RELATED (GRAPH LINKS)
    # =========================================================

    direct = [
        n for n in related_nodes
        if isinstance(n, dict) and n.get("url")
    ][:6]

    if direct:

        links = "\n".join(
            f'    <a class="semantic-chip" href="{n["url"]}">{get_display_title(n)}</a>'
            for n in direct
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
    # TIER 1 — FALLBACK (CONCEPT OVERLAP WITH FULL GRAPH)
    # =========================================================

    fallback = []

    for n in graph.values():
        if not isinstance(n, dict):
            continue

        node_concepts = set(n.get("concepts", []))

        # overlap strength signal
        if node_concepts & seed:
            fallback.append(n)

    fallback = fallback[:6]

    if fallback:

        links = "\n".join(
            f'    <a class="semantic-chip" href="{n.get("url", "#")}">{get_display_title(n)}</a>'
            for n in fallback
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
    # TIER 2 — EMPTY STATE (TRUE DEAD END ONLY)
    # =========================================================

    return """
<section class="semantic-block related-paths">

  <h3>Further paths to follow...</h3>

  <div class="semantic-cloud">
    <span class="semantic-chip muted">No related content available yet — this page stands alone.</span>
  </div>

</section>
""".strip()

    # =========================================================
    # TIER 2: PURE EMPTY STATE (rare)
    # =========================================================
    return """
<section class="semantic-block related-paths">

  <h3>Further paths to follow...</h3>

  <div class="semantic-cloud">
    <span class="semantic-chip muted">No related content available yet — this page stands alone.</span>
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

    print("\n🧭 GRAPH KEY SAMPLE (first 20 keys):")
    for i, k in enumerate(graph.keys()):
        print(" ", repr(k))
        if i > 20:
            break
    
    updated = 0

    html_files = [
        p for p in ROOT.rglob("*.html")
        if "assets" not in p.parts
    ]

    for path in html_files:

        url = file_to_url(path)
        graph_key = normalize_url(url)

        node = graph.get(graph_key)

        
        print("\n📄 FILE → URL DEBUG")
        print("path:", path)
        print("file_to_url:", file_to_url(path))
        print("normalized:", normalize_url(file_to_url(path)))

        
        if node is None:
            print("\n==============================")
            print("MISSING NODE")
            print("url       :", repr(url))
            print("graph_key :", repr(graph_key))

            print("\nClosest graph keys:")

            for k in list(graph.keys())[:10]:
                print(repr(k))

            print("==============================\n")
            continue

        
        related_urls = node.get("related", [])
        related_nodes = []



        
        for u in related_urls:

            if not isinstance(u, str):
                continue

            u = u.strip()
            if not u:
                continue

            key = normalize_url(u)

            n = graph.get(key)



            
            if not isinstance(n, dict):
                continue

            if not n.get("url"):
                continue

            if not n.get("title"):
                n["title"] = get_display_title(n)

            related_nodes.append(n)

        
        html = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        # HARD GUARD: do not render empty related sections
        if not related_nodes:
            print("⚠️ empty related section:", url)
            continue

        block = render_block_with_graph(
            related_nodes,
            graph,
            current_url=url  # REQUIRED: ensures correct context binding
        )

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
