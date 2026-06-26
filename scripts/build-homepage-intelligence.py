#!/usr/bin/env python3

import os
import json
from pathlib import Path
from collections import defaultdict

# =========================================================
# PATHS
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SAL_FILE = os.path.join(ROOT, "semantic-salience.json")
OUTPUT_FILE = os.path.join(ROOT, "homepage-intelligence.json")


# =========================================================
# LOAD
# =========================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# =========================================================
# DISPLAY TITLE
# =========================================================

def get_display_title(node):
    if not node:
        return ""

    title = node.get("title")

    if isinstance(title, str) and title.strip():
        return title.strip()

    url = node.get("url", "")
    return url.rstrip("/").split("/")[-1]


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_url(url):
    if not isinstance(url, str):
        return None

    url = url.strip()

    if url.startswith("/"):
        url = "https://unboundhealing.org" + url

    if not url.startswith("https://unboundhealing.org/"):
        return None

    return url


def valid_url(url):
    url = normalize_url(url)
    if not url:
        return False

    tail = url.rstrip("/").split("/")[-1]

    if tail.isdigit():
        return False

    if "assets" in url or "images" in url:
        return False

    return True


# =========================================================
# CONCEPT CLEANER
# =========================================================

def clean_concept(c):
    if not isinstance(c, str):
        return None

    c = c.strip().lower()
    if not c:
        return None

    if c in {"assets", "images"}:
        return None

    if c.isdigit():
        return None

    return c.replace("-", " ")


# =========================================================
# DEBUG
# =========================================================

def debug(nodes, edges, data):

    print("\n===== HOMEPAGE DEBUG =====")

    pg = data.get("page_graph", {})

    print("PAGE_GRAPH SIZE:", len(pg))

    for i, k in enumerate(pg.keys()):
        print(k)
        if i >= 5:
            break

    print("\nNODE COUNT:", len(nodes))
    print("EDGE COUNT:", len(edges))

    if nodes:
        first_key = next(iter(nodes))
        print("\nFIRST NODE KEY:", first_key)
        print(json.dumps(nodes[first_key], indent=2)[:1200])

    print("\nFIRST 5 EDGES:")
    for e in edges[:5]:
        print(e)

    print("\n===== END DEBUG =====\n")


# =========================================================
# CORE BUILDER
# =========================================================

def build(nodes, edges, page_graph):

    concept_freq = defaultdict(int)

    # -------------------------
    # concepts (truth layer metadata)
    # -------------------------

    for n in nodes.values():
        concepts = n.get("concepts", [])
        if not isinstance(concepts, list):
            continue

        for c in concepts:
            c = clean_concept(c)
            if c:
                concept_freq[c] += 1

    # -------------------------
    # ARISINGS (PAGE_GRAPH = TRUTH SOURCE)
    # -------------------------

    arisings = []

    for url, meta in page_graph.items():

        if not valid_url(url):
            continue

        url = normalize_url(url)
        if not url:
            continue

        score = 0.0

        if isinstance(meta, dict):
            score += len(meta.get("related", [])) * 1.5
            score += len(meta.get("concepts", [])) * 1.0

        node = nodes.get(url)

        arisings.append({
            "url": url,
            "title": get_display_title(node),
            "score": score
        })

    arisings.sort(key=lambda x: -x["score"])
    arisings = arisings[:3]

    # -------------------------
    # INSPIRATIONS
    # -------------------------

    inspirations = []

    for c, f in sorted(concept_freq.items(), key=lambda x: -x[1]):

        inspirations.append({
            "concept": c.title(),
            "frequency": f
        })

        if len(inspirations) == 3:
            break

    return {
        "arising_observations": arisings,
        "essential_inspirations": inspirations,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


# =========================================================
# RENDER
# =========================================================

def render(data):

    arisings = data.get("arising_observations", [])
    insp = data.get("essential_inspirations", [])

    if arisings:
        arisings_html = "\n".join(
            f'<a class="semantic-chip" href="{a["url"]}">{a["title"]}</a>'
            for a in arisings
        )
    else:
        arisings_html = '<span class="semantic-chip muted">No observations</span>'

    if insp:
        insp_html = "\n".join(
            f'<span class="semantic-chip">{i["concept"]}</span>'
            for i in insp
        )
    else:
        insp_html = '<span class="semantic-chip muted">No inspirations</span>'

    return f"""
<section class="semantic-block homepage-intelligence">

  <h3>Arising observations</h3>

  <div class="semantic-cloud">
    {arisings_html}
  </div>

  <div style="height:42px"></div>

  <h3>Essential inspirations</h3>

  <div class="semantic-cloud">
    {insp_html}
  </div>

</section>
""".strip()


# =========================================================
# MAIN
# =========================================================

def main():

    data = load_json(SAL_FILE)

    nodes = data.get("nodes", {})
    edges = data.get("edges", [])
    page_graph = data.get("page_graph", {})

    debug(nodes, edges, data)

    built = build(nodes, edges, page_graph)

    output = {
        "homepage_intelligence": built,
        "source": "semantic-salience",
        "status": "ok"
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    html_block = render(built)

    index = Path(ROOT) / "index.html"

    html = index.read_text(encoding="utf-8")

    html = html.replace(
        '<div id="homepage-intelligence"></div>',
        html_block
    )

    index.write_text(html, encoding="utf-8")

    print("DONE")


if __name__ == "__main__":
    main()
