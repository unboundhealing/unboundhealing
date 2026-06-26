#!/usr/bin/env python3

import json
import os
from pathlib import Path

# =========================================================
# ROOT
# =========================================================

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))
SAL_FILE = ROOT / "semantic-salience.json"


# =========================================================
# CACHE (GLOBAL STATE)
# =========================================================

CACHE = {}


# =========================================================
# LOAD
# =========================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# NORMALIZATION (MATCH SALIENCE EXACTLY)
# =========================================================

def normalize_url(url: str) -> str:
    if not isinstance(url, str):
        return ""

    url = url.strip()

    if not url.startswith("http"):
        return ""

    if not url.endswith("/"):
        url += "/"

    return url


# =========================================================
# DISPLAY TITLE
# =========================================================

def get_title(node, url=None):
    if isinstance(node, dict):
        t = node.get("title")
        if isinstance(t, str) and t.strip():
            return t.strip()

    if url:
        return url.rstrip("/").split("/")[-1]

    return ""


# =========================================================
# NODE RESOLUTION (CRITICAL FIX LAYER)
# =========================================================

def resolve_node(url, nodes, graph):
    """
    SINGLE SOURCE OF TRUTH PER URL
    Never returns mixed structures.
    """

    url = normalize_url(url)

    raw = graph.get(url) or nodes.get(url)

    if not isinstance(raw, dict):
        return None

    return {
        "url": url,
        "title": raw.get("title", ""),
        "concepts": raw.get("concepts", []) or [],
        "related": raw.get("related", []) or []
    }


# =========================================================
# SCORING (PURE CONSUMER LOGIC)
# =========================================================

def score_node(candidate, seed):
    if not candidate:
        return 0

    concepts = set(candidate.get("concepts", []))
    overlap = len(concepts & seed)

    connectivity = len(candidate.get("related", []))
    richness = len(concepts)

    return (
        overlap * 3.0 +
        connectivity * 1.5 +
        richness * 0.5
    )


# =========================================================
# RELATED CONTENT BUILDER
# =========================================================

def get_related(url, nodes, page_graph):

    if url in CACHE:
        return CACHE[url]

    node = nodes.get(url)
    if not node:
        return []

    seed = set(node.get("concepts", []))

    candidates = set()

    meta = page_graph.get(url, {})
    for r in meta.get("related", []):
        candidates.add(r)

    for concept in seed:
        for u, n in nodes.items():
            if concept in n.get("concepts", []):
                candidates.add(u)

    scored = []

    for c in candidates:
        n = nodes.get(c)
        if not n:
            continue

        concepts = set(n.get("concepts", []))

        overlap = len(seed & concepts)
        graph_bonus = len(page_graph.get(c, {}).get("related", []))

        score = (
            overlap * 3.0 +
            graph_bonus * 1.5
        )

        scored.append((score, c))

    scored.sort(reverse=True)

    result = [c for _, c in scored[:6]]

    CACHE[url] = result

    return result


# =========================================================
# HTML RENDER
# =========================================================

def render_block(nodes):
    if not nodes:
        return ""

    links = "\n".join(
        f'    <a class="semantic-chip" href="{n["url"]}">{n["title"]}</a>'
        for n in nodes
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
# FILE URL RESOLUTION (OPTIONAL UTILITY)
# =========================================================

def resolve_file_url(path, graph, nodes):
    """
    OPTIONAL helper (NOT nested, NOT inside main).
    """

    for url in graph.keys():
        if path.as_posix().replace("index.html", "").endswith(
            url.replace("https://unboundhealing.org/", "")
        ):
            return url

    return None


# =========================================================
# MAIN
# =========================================================

def main():

    data = load_json(SAL_FILE)

    nodes = data["nodes"]
    page_graph = data["page_graph"]


    # =====================================================
    # FILE DISCOVERY (MUST EXIST BEFORE LOOP)
    # =====================================================
    html_files = [
        p for p in ROOT.rglob("*.html")
        if "assets" not in p.parts
    ]

    
    seen = set()

    for path in html_files:

        url = resolve_file_url(path, nodes, page_graph)

        if not url or url in seen:
            continue

        seen.add(url)

        related = get_related(url, nodes, page_graph)


def read_html(path):
    return path.read_text(encoding="utf-8", errors="ignore")
        
    html = read_html(path)


        block = render_related(url, related)

        html = inject(html, block)

        path.write_text(html)

        print("CURRENT PAGE:", url)
        print("RELATED COUNT:", len(related))

        if not related:
            continue

        block = render_block(related)

        if '<div id="related-content">' not in html:
            continue

        new_html = html.replace(
            '<div id="related-content"></div>',
            block
        )

        path.write_text(new_html, encoding="utf-8")

        updated += 1
        print("🔗 injected:", url)

    print("\n========================")
    print("RELATED CONTENT COMPLETE")
    print("PAGES UPDATED:", updated)


if __name__ == "__main__":
    main()
