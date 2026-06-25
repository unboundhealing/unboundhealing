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
# LOADER
# =========================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# SAFE ACCESSORS
# =========================================================

def get_nodes(data):

    nodes = data.get("nodes", {})

    if not isinstance(nodes, dict):
        return {}

    return nodes


def get_edges(data):

    edges = data.get("edges", [])

    if not isinstance(edges, list):
        return []

    cleaned = []

    for e in edges:

        if not isinstance(e, dict):
            continue

        a = e.get("a")
        b = e.get("b")

        if a is None or b is None:
            continue

        cleaned.append({
            "a": str(a),
            "b": str(b),
            "weight": float(e.get("weight", 1))
        })

    return cleaned


# =========================================================
# HOMEPAGE INTELLIGENCE DERIVATION
# =========================================================

def build_homepage_intelligence(nodes, edges):

    concept_frequency = defaultdict(int)
    node_degree = defaultdict(float)

    # -----------------------------------------
    # concept frequency
    # -----------------------------------------

    for node in nodes.values():

        concepts = node.get("concepts", [])

        if not isinstance(concepts, list):
            continue

        for c in concepts:
            concept_frequency[c] += 1

    # -----------------------------------------
    # connectivity
    # -----------------------------------------

    for e in edges:

        a = e["a"]
        b = e["b"]
        w = e["weight"]

        node_degree[a] += w
        node_degree[b] += w

    # -----------------------------------------
    # top concepts
    # -----------------------------------------

    top_concepts = sorted(
        concept_frequency.items(),
        key=lambda x: (-x[1], x[0])
    )[:10]

    # -----------------------------------------
    # top hubs
    # -----------------------------------------

    top_hubs = sorted(
        node_degree.items(),
        key=lambda x: (-x[1], x[0])
    )[:10]

    return {
        "top_concepts": [
            {"concept": c, "frequency": f}
            for c, f in top_concepts
        ],
        "top_hubs": [
            {"node": n, "score": s}
            for n, s in top_hubs
        ],
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


# =========================================================
# HOMEPAGE RENDERING
# =========================================================

def prettify_url(url):

    if not url:
        return "Untitled"

    path = (
        url.replace("https://unboundhealing.org", "")
        .strip("/")
    )

    if not path:
        return "Home"

    slug = path.split("/")[-1]

    return slug.replace("-", " ").title()


def render_homepage(intel):

    data = intel.get("homepage_intelligence", {})

    concepts = data.get("top_concepts", [])
    hubs = data.get("top_hubs", [])

    concepts_html = "\n".join(
        f'<span class="chip">{c["concept"]}</span>'
        for c in concepts
    )

    hubs_html = "\n".join(
        f'<a class="chip" href="{h["node"]}">{prettify_url(h["node"])}</a>'
        for h in hubs
    )

    return f"""
<section class="homepage-intelligence">

  <h3>Arising Concepts</h3>

  <div class="chip-cloud">
    {concepts_html}
  </div>

  <h3>Structural Hubs</h3>

  <div class="chip-cloud">
    {hubs_html}
  </div>

</section>
""".strip()


# =========================================================
# HOMEPAGE DETECTION
# =========================================================

def is_root_homepage(path: Path):

    return path.resolve() == Path(ROOT, "index.html").resolve()


# =========================================================
# HOMEPAGE INJECTION
# =========================================================

def inject_homepage(block):

    homepage_path = Path(ROOT) / "index.html"

    if not homepage_path.exists():
        print("⚠️ homepage missing")
        return 0

    html = homepage_path.read_text(encoding="utf-8")

    placeholder = '<div id="homepage-intelligence"></div>'

    if placeholder not in html:
        print("⚠️ homepage placeholder missing")
        return 0

    html = html.replace(placeholder, block)

    homepage_path.write_text(html, encoding="utf-8")

    print("🏠 injected homepage intelligence:", homepage_path)

    return 1


# =========================================================
# MAIN
# =========================================================

def main():

    data = load_json(SAL_FILE)

    print()
    print("INTELLIGENCE INPUT KEYS:")
    print(data.keys())

    print()
    print("PAGE_GRAPH COUNT:")
    print(len(data.get("page_graph", {})))

    nodes = get_nodes(data)
    edges = get_edges(data)

    homepage = build_homepage_intelligence(
        nodes,
        edges
    )

    output = {
        "homepage_intelligence": homepage,
        "source": "semantic-salience",
        "consumer_model": "read-only-projection",
        "status": "ok"
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("🏠 homepage-intelligence built successfully")
    print(f"📦 nodes: {len(nodes)}")
    print(f"🔗 edges: {len(edges)}")

    # -----------------------------------------
    # render homepage block
    # -----------------------------------------

    homepage_block = render_homepage(output)

    # -----------------------------------------
    # inject homepage
    # -----------------------------------------

    updated = inject_homepage(homepage_block)

    print()
    print("========================")
    print("HOMEPAGE COMPLETE")
    print("PAGES UPDATED:", updated)


if __name__ == "__main__":
    main()
