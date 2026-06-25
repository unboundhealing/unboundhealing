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
    return nodes if isinstance(nodes, dict) else {}


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

        if not a or not b:
            continue

        cleaned.append({
            "a": str(a),
            "b": str(b),
            "weight": float(e.get("weight", 1))
        })

    return cleaned


# =========================================================
# CLEANING
# =========================================================

def clean_concept(c):
    if not isinstance(c, str):
        return None

    c = c.strip().lower()
    if not c:
        return None

    # HARD FILTERS
    if c in {"assets", "images"}:
        return None

    # slug normalization
    c = c.replace("-", " ")

    return c


def section_title(text):
    if not text:
        return ""
    return text[0].upper() + text[1:]


def prettify_url(url):
    if not url:
        return "Untitled"

    path = url.replace("https://unboundhealing.org", "").strip("/")

    if not path:
        return "Home"

    slug = path.split("/")[-1]
    return slug.replace("-", " ").title()


# =========================================================
# HOMEPAGE INTELLIGENCE
# =========================================================

def build_homepage_intelligence(nodes, edges):

    concept_frequency = defaultdict(int)
    node_degree = defaultdict(float)

    # -------------------------
    # concepts
    # -------------------------

    for node in nodes.values():
        concepts = node.get("concepts", [])
        if not isinstance(concepts, list):
            continue

        for c in concepts:
            c = clean_concept(c)
            if not c:
                continue
            concept_frequency[c] += 1

    # -------------------------
    # connectivity
    # -------------------------

    for e in edges:
        a = e["a"]
        b = e["b"]
        w = e["weight"]

        node_degree[a] += w
        node_degree[b] += w

    # -------------------------
    # top concepts (STRICT CAP 3)
    # -------------------------

    seen = set()
    top_concepts = []

    for c, f in sorted(concept_frequency.items(), key=lambda x: (-x[1], x[0])):
        if c in seen:
            continue
        seen.add(c)
        top_concepts.append({"concept": c, "frequency": f})
        if len(top_concepts) >= 3:
            break

    # -------------------------
    # top hubs (STRICT CAP 3)
    # -------------------------

    top_hubs = []

    for n, s in sorted(node_degree.items(), key=lambda x: (-x[1], x[0])):
        label = prettify_url(n)

        # filter noise labels
        if any(x in label.lower() for x in ["assets", "images"]):
            continue

        top_hubs.append({"node": n, "label": label, "score": s})

        if len(top_hubs) >= 3:
            break

    return {
        "top_concepts": top_concepts,
        "top_hubs": top_hubs,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


# =========================================================
# RENDERING
# =========================================================

def render_homepage(intel):

    data = intel.get("homepage_intelligence", {})

    concepts = data.get("top_concepts", [])
    hubs = data.get("top_hubs", [])

    concepts_html = "\n".join(
        f'<span class="chip">{c["concept"].title()}</span>'
        for c in concepts
    )

    hubs_html = "\n".join(
        f'<a class="chip" href="{h["node"]}">{h.get("label", "Untitled")}</a>'
        for h in hubs
    )

    return f"""
<section class="homepage-intelligence">

  <h3>{section_title("arising concepts...")}</h3>

  <div class="chip-cloud">
    {concepts_html}
  </div>

  <h3>{section_title("essential inspirations...")}</h3>

  <div class="chip-cloud">
    {hubs_html}
  </div>

</section>
""".strip()


# =========================================================
# OUTPUT
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

    nodes = get_nodes(data)
    edges = get_edges(data)

    homepage = build_homepage_intelligence(nodes, edges)

    output = {
        "homepage_intelligence": homepage,
        "source": "semantic-salience",
        "consumer_model": "read-only-projection",
        "status": "ok"
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("🏠 homepage-intelligence built successfully")
    print(f"📦 nodes: {len(nodes)}")
    print(f"🔗 edges: {len(edges)}")

    block = render_homepage(output)

    updated = inject_homepage(block)

    print("========================")
    print("HOMEPAGE COMPLETE")
    print("PAGES UPDATED:", updated)


if __name__ == "__main__":
    main()
