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
# SAFE ACCESS
# =========================================================

def get_nodes(data):
    return data.get("nodes", {}) if isinstance(data.get("nodes"), dict) else {}


def get_edges(data):
    edges = data.get("edges", [])
    if not isinstance(edges, list):
        return []

    out = []

    for e in edges:
        if not isinstance(e, dict):
            continue

        a = e.get("a")
        b = e.get("b")

        if not a or not b:
            continue

        out.append({
            "a": str(a),
            "b": str(b),
            "weight": float(e.get("weight", 1))
        })

    return out


# =========================================================
# CLEANING LAYER (CRITICAL FIX)
# =========================================================

def clean_concept(c):
    if not isinstance(c, str):
        return None

    c = c.strip().lower()

    # HARD FILTERS
    if not c:
        return None
    if c in {"assets", "images"}:
        return None
    if c.isdigit():
        return None

    # normalize slug fragments
    c = c.replace("-", " ").strip()

    if len(c) < 2:
        return None

    return c


def is_valid_url(url):
    if not url or not isinstance(url, str):
        return False

    if "assets" in url or "images" in url:
        return False

    if url.rstrip("/").endswith("/1"):
        return False

    if not url.startswith("https://unboundhealing.org/"):
        return False

    return True


def prettify_url(url):
    if not url:
        return ""

    url = str(url)
    path = url.replace("https://unboundhealing.org", "").strip("/")

    if not path:
        return "Home"

    slug = path.split("/")[-1]

    if slug.isdigit() or slug in {"assets", "images"}:
        return ""

    return slug.replace("-", " ").title()


def section_title(text):
    if not text:
        return ""
    return text[0].upper() + text[1:].lower()


# =========================================================
# BUILD INTELLIGENCE
# =========================================================

def build_homepage_intelligence(nodes, edges):

    concept_frequency = defaultdict(int)
    node_degree = defaultdict(float)

    # -------------------------
    # concepts (cleaned)
    # -------------------------

    for node in nodes.values():
        concepts = node.get("concepts", [])
        if not isinstance(concepts, list):
            continue

        for c in concepts:
            c = clean_concept(c)
            if c:
                concept_frequency[c] += 1

    # -------------------------
    # graph connectivity
    # -------------------------

    for e in edges:
        a, b, w = e["a"], e["b"], e["weight"]

        node_degree[a] += w
        node_degree[b] += w

    # -------------------------
    # TOP CONCEPTS (STRICT: 3 ONLY)
    # -------------------------

    top_concepts = []
    seen = set()

    for c, f in sorted(concept_frequency.items(), key=lambda x: (-x[1], x[0])):
        if c in seen:
            continue
        seen.add(c)

        top_concepts.append({
            "concept": c,
            "frequency": f
        })

        if len(top_concepts) >= 3:
            break

    # -------------------------
    # TOP HUBS (STRICT: 3 ONLY + VALIDATED URLS)
    # -------------------------

    top_hubs = []

    for n, s in sorted(node_degree.items(), key=lambda x: (-x[1], x[0])):

        if not is_valid_url(n):
            continue

        label = prettify_url(n)
        if not label:
            continue

        top_hubs.append({
            "node": n,
            "label": label,
            "score": s
        })

        if len(top_hubs) >= 3:
            break

    return {
        "top_concepts": top_concepts,
        "top_hubs": top_hubs,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


# =========================================================
# RENDER LAYER (CSS SAFE, STRUCTURED)
# =========================================================

def render_homepage(intel):

    data = intel.get("homepage_intelligence", {})

    concepts = data.get("top_concepts", [])
    hubs = data.get("top_hubs", [])

    # -------------------------
    # concepts (safe chips)
    # -------------------------

    concepts_html = "\n".join(
        f'<span class="chip">{c["concept"].title()}</span>'
        for c in concepts
        if isinstance(c.get("concept"), str)
    )

    # -------------------------
    # hubs (safe links)
    # -------------------------

    hubs_html = "\n".join(
        f'<a class="chip" href="{h["node"]}">{h.get("label","")}</a>'
        for h in hubs
        if is_valid_url(h.get("node"))
    )

    return f"""
<section class="homepage-intelligence">

  <h3 class="intelligence-title">{section_title("arising observations...")}</h3>

  <div class="chip-cloud">
    {concepts_html}
  </div>

  <h3 class="intelligence-title">{section_title("essential inspirations...")}</h3>

  <div class="chip-cloud">
    {hubs_html}
  </div>

</section>
""".strip()


# =========================================================
# INJECTION
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
