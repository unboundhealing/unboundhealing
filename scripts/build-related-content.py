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

    # Relative URL → make canonical
    if not url.startswith("http"):
        url = "https://unboundhealing.org/" + url.lstrip("/")

    # Collapse duplicate slashes (not after https:)
    url = re.sub(r"(?<!:)//+", "/", url)

    # Trailing slash
    if not url.endswith("/"):
        url += "/"

    # enforce canonical trailing slash rule
    url = url.rstrip("/") + "/"
    
    return url

# =========================================================
# RELATED BLOCK RENDERER
# =========================================================

def render_block_with_graph(related_nodes, graph, current_url):

    current_graph_node = graph.get(current_url)

    seed = set()
    if isinstance(current_graph_node, dict):
        seed |= set(current_graph_node.get("concepts", []))

    # =========================================================
    # TIER 0 — DIRECT RELATED
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
    # TIER 1 — FALLBACK
    # =========================================================

    fallback = []

    for n in graph.values():
        if not isinstance(n, dict):
            continue

        node_concepts = set(n.get("concepts", []))

        if node_concepts & seed:
            fallback.append(n)

    fallback = sorted(
        fallback,
        key=lambda n: len(set(n.get("concepts", [])) & seed),
        reverse=True
    )[:6]

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
    # TIER 2 — EMPTY STATE
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

        replacement_soup = BeautifulSoup(block, "html.parser")

        replacement_node = replacement_soup.find("section", class_="semantic-block")

        if replacement_node is None:
            return html, False

        # safer re-serialization boundary
        safe_node = BeautifulSoup(str(replacement_node), "html.parser")

        placeholder.replace_with(safe_node)

        return str(soup), True

    except Exception as e:
        print("⚠️ replacement error in placeholder injection:", e)
        return html, False


# =========================================================
# MAIN
# =========================================================

def main():
    data = load_json()

    print("\n===== FIRST NODE =====")
    nodes = data["nodes"]

    print(type(nodes))

    if isinstance(nodes, dict):
        first_key = next(iter(nodes))
        print("key:", first_key)
        print(json.dumps(nodes[first_key], indent=2))

    elif isinstance(nodes, list):
        print(json.dumps(nodes[0], indent=2))

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


        
        page_node = graph.get(graph_key) or nodes.get(graph_key)

        if not isinstance(page_node, dict):
            print("MISSING NODE:", graph_key)
            continue


        related_urls = page_node.get("related", [])

        related_nodes = []   # 🔴 MUST ALWAYS BE LIST

        for u in related_urls:

            if not isinstance(u, str):
                continue

            key = normalize_url(u)

            candidate_node = graph.get(key) or nodes.get(key)

            if not isinstance(candidate_node, dict):
                continue

            candidate_node.append(candidate_node)

            print("append:", candidate_node.get("url"))
            print("current length:", len(related_nodes))
        
        
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
            current_url=url
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
