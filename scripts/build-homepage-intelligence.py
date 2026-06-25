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
# URL NORMALIZATION (CRITICAL FIX)
# =========================================================

def normalize_url(url):
    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    # absolute
    if url.startswith("https://unboundhealing.org"):
        return url

    # relative
    if url.startswith("/"):
        return "https://unboundhealing.org" + url

    return None


def is_valid_url(url):
    url = normalize_url(url)
    if not url:
        return False

    if "assets" in url or "images" in url:
        return False

    last = url.rstrip("/").split("/")[-1]
    if last.isdigit():
        return False

    return True


def title_from_url(url):
    url = normalize_url(url)
    if not url:
        return ""

    path = url.replace("https://unboundhealing.org", "").strip("/")
    if not path:
        return "Home"

    slug = path.split("/")[-1]
    return slug.replace("-", " ").strip().title()


# =========================================================
# CLEANING
# =========================================================

def clean_text(s):
    if not isinstance(s, str):
        return None

    s = s.strip()

    # remove artifact noise
    s = s.replace("(((", "").replace(")))", "")
    s = s.replace("((", "").replace("))", "")
    s = s.replace("(( ))", "").replace("(())", "")

    if not s:
        return None

    if s.isdigit():
        return None

    if s.lower() in {"assets", "images"}:
        return None

    return s


def clean_concept(c):
    c = clean_text(c)
    if not c:
        return None

    c = c.lower().replace("-", " ").strip()

    if len(c) < 2:
        return None

    return c


# =========================================================
# INTELLIGENCE BUILD
# =========================================================

def build_homepage_intelligence(nodes, edges):

    concept_freq = defaultdict(int)
    node_score = defaultdict(float)

    # -------------------------
    # concepts (from nodes only)
    # -------------------------

    for node in nodes.values():
        concepts = node.get("concepts", [])
        if not isinstance(concepts, list):
            continue

        for c in concepts:
            c = clean_concept(c)
            if c:
                concept_freq[c] += 1

    # -------------------------
    # graph scoring
    # -------------------------

    for e in edges:
        a, b, w = e["a"], e["b"], e["weight"]
        node_score[a] += w
        node_score[b] += w

    # -------------------------
    # ARISINGS (STRICT LINKS ONLY)
    # -------------------------

    arisings = []
    seen = set()

    for url, score in sorted(node_score.items(), key=lambda x: (-x[1], x[0])):

        if not is_valid_url(url):
            continue

        url = normalize_url(url)
        if not url or url in seen:
            continue

        title = title_from_url(url)
        if not title:
            continue

        seen.add(url)

        arisings.append({
            "url": url,
            "title": title,
            "score": score
        })

        if len(arisings) >= 3:
            break

    # -------------------------
    # ESSENTIAL INSPIRATIONS (CONCEPTS ONLY)
    # -------------------------

    inspirations = []
    seen_c = set()

    for c, f in sorted(concept_freq.items(), key=lambda x: (-x[1], x[0])):

        if c in seen_c:
            continue

        seen_c.add(c)

        inspirations.append({
            "concept": c.title(),
            "frequency": f
        })

        if len(inspirations) >= 3:
            break

    return {
        "arising_observations": arisings,
        "essential_inspirations": inspirations,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


# =========================================================
# RENDER (CSS-COMPATIBLE + STRUCTURE FIXED)
# =========================================================

def section_title(text):
    if not text:
        return ""
    return text.strip().capitalize()


def render_homepage(intel):

    data = intel.get("homepage_intelligence", {})

    arisings = data.get("arising_observations", [])
    inspirations = data.get("essential_inspirations", [])

    # -------------------------
    # ARISINGS (REAL LINKS ONLY)
    # -------------------------

    arisings_html = "\n".join(
        f'<a class="chip semantic-chip" href="{a["url"]}">{a["title"]}</a>'
        for a in arisings
        if normalize_url(a.get("url"))
    )

    if not arisings_html:
        arisings_html = '<span class="chip semantic-chip muted">No observations available</span>'

    # -------------------------
    # INSPIRATIONS (CONCEPTS)
    # -------------------------

    insp_html = "\n".join(
        f'<span class="chip semantic-chip">{i["concept"]}</span>'
        for i in inspirations
    )

    if not insp_html:
        insp_html = '<span class="chip semantic-chip muted">No inspirations available</span>'

    return f"""
<section class="homepage-intelligence semantic-block">

  <h3>Arising observations</h3>

  <div class="chip-cloud semantic-cloud">
    {arisings_html}
  </div>

  <div style="height:28px"></div>

  <h3>Essential inspirations</h3>

  <div class="chip-cloud semantic-cloud">
    {insp_html}
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

    intel = build_homepage_intelligence(nodes, edges)

    output = {
        "homepage_intelligence": intel,
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
