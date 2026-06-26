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
    """
    Fully ephemeral scoring layer.
    Does NOT modify truth layer.
    """

    if not candidate:
        return 0

    concepts = set(candidate.get("concepts", []))
    overlap = len(concepts & seed)

    url_bonus = 1 if candidate.get("url") else 0

    return (
        overlap * 3.0 +
        url_bonus * 1.0
    )


# =========================================================
# RELATED CONTENT BUILDER
# =========================================================

def build_related_for_page(url, nodes, graph):
    """
    Resolve → score → return sorted candidates
    """

    current = resolve_node(url, nodes, graph)
    if not current:
        return []

    seed = set(current.get("concepts", []))

    candidates = []

    # -----------------------------------------------------
    # expand via page_graph relationships
    # -----------------------------------------------------

    for u in current.get("related", []):
        n = resolve_node(u, nodes, graph)
        if n:
            candidates.append(n)

    # -----------------------------------------------------
    # fallback enrichment (graph-wide scan)
    # -----------------------------------------------------

    if not candidates:
        for u in graph.keys():
            n = resolve_node(u, nodes, graph)
            if n:
                candidates.append(n)

    # -----------------------------------------------------
    # scoring
    # -----------------------------------------------------

    scored = [
        (score_node(n, seed), n)
        for n in candidates
    ]

    scored.sort(key=lambda x: -x[0])

    return [n for _, n in scored[:6]]


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
# MAIN
# =========================================================

def main():
    data = load_json(SAL_FILE)

    nodes = data.get("nodes", {})
    graph = data.get("page_graph", {})

    html_files = [
        p for p in ROOT.rglob("*.html")
        if "assets" not in p.parts
    ]

    updated = 0

    for path in html_files:

        html = path.read_text(encoding="utf-8", errors="ignore")


    def resolve_file_url(path, graph, nodes):
        # derive ALL truth from existing system
        for url in graph.keys():
            if path.as_posix().replace("index.html", "").endswith(url.replace("https://unboundhealing.org/", "")):
                return url

        return None
        
        
        related = build_related_for_page(url, nodes, graph)

        print("\nCURRENT PAGE:", url)
        print("RELATED COUNT:", len(related))

            if not related:
                continue

        block = render_block(related)

            if "<div id=\"related-content\">" not in html:
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
