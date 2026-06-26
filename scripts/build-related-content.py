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

def get_node(url, nodes):
    url = normalize_url(url)
    return nodes.get(url)


def get_related_urls(url, graph):
    url = normalize_url(url)
    return graph.get(url, {}).get("related", [])


def build_view(url, nodes, graph):
    node = get_node(url, nodes)
    if not node:
        return None

    seed = set(node.get("concepts", []))

    related_urls = get_related_urls(url, graph)

    candidates = []
    
    for u in related_urls:
        n = nodes.get(u)
        if not n:
            continue

        candidates.append({
            "url": u,
            "title": n.get("title", ""),
            "concepts": n.get("concepts", []),
            "graph_neighbors": len(graph.get(u, {}).get("related", [])),
            "word_count": n.get("word_count", 0),
            "depth": u.count("/")
        })    
        
    scored = [
        (score_node(c, seed), c)
        for c in candidates
    ]

    scored.sort(key=lambda x: -x[0])

    related = [c["url"] for _, c in scored[:6]]

    return {
        "url": url,
        "title": node.get("title", ""),
        "concepts": node.get("concepts", []),
        "related": related
    }


# =========================================================
# SCORING (PURE CONSUMER LOGIC)
# =========================================================

def score_node(candidate, seed):
    overlap = len(seed & set(candidate["concepts"]))

    return (
        overlap * 3.0 +
        candidate["graph_neighbors"] * 1.5 +
        candidate["depth"] * 0.8
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

    return [
    {
        "url": c,
        "title": nodes.get(c, {}).get("title", c)
    }
    for _, c in scored[:6]
    ]
    
    CACHE[url] = result

    return result


# =========================================================
# HTML RENDER
# =========================================================

def render_block(related):
    if not related:
        return ""

    links = "\n".join(
        f'    <a class="semantic-chip" href="{n["url"]}">{n["title"]}</a>'
        for n in related if isinstance(n, dict)
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
    
    updated = 0
    
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

        html = read_html(path)

        block = render_block(related)

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


def read_html(path):
    return path.read_text(encoding="utf-8", errors="ignore")


if __name__ == "__main__":
    main()
