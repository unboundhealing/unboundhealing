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




print("\n===== HOMEPAGE DEBUG =====")

print("PAGE_GRAPH KEYS:")
print(len(data.get("page_graph", {})))

for i, k in enumerate(data.get("page_graph", {}).keys()):
    print(k)
    if i >= 5:
        break

print("\nSALIENCE SAMPLE:")
print(list(data.get("salience", {}).items())[:10])

print("==========================\n")




# =========================================================
# NORMALIZATION LAYER
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


def title_from_url(url):
    url = normalize_url(url)
    if not url:
        return ""

    slug = url.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").title()


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
# CORE BUILDER
# =========================================================

def build(nodes, edges):

    concept_freq = defaultdict(int)
    score = defaultdict(float)

    # concepts
    for n in nodes.values():
        concepts = n.get("concepts", [])
        if not isinstance(concepts, list):
            continue

        for c in concepts:
            c = clean_concept(c)
            if c:
                concept_freq[c] += 1

    # edges
    for e in edges:
        a, b, w = e["a"], e["b"], e["weight"]
        score[a] += w
        score[b] += w

    # =====================================================
    # ARISINGS (STRICT: real articles only)
    # =====================================================

    arisings = []
    seen = set()

    for url, s in sorted(score.items(), key=lambda x: -x[1]):

        if not valid_url(url):
            continue

        url = normalize_url(url)

        if url in seen:
            continue

        seen.add(url)

        arisings.append({
            "url": url,
            "title": title_from_url(url),
            "score": s
        })

        if len(arisings) == 3:
            break

    # =====================================================
    # INSPIRATIONS (STRICT: concepts only)
    # =====================================================

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
# RENDER (CSS CONTRACT FIXED)
# =========================================================

def render(data):

    arisings = data.get("arising_observations", [])
    insp = data.get("essential_inspirations", [])

    # ALWAYS guarantee content presence (fix empty section bug)
    if not arisings:
        arisings_html = '<span class="semantic-chip muted">No observations</span>'
    else:
        arisings_html = "\n".join(
            f'<a class="semantic-chip" href="{a["url"]}">{a["title"]}</a>'
            for a in arisings
        )

    if not insp:
        insp_html = '<span class="semantic-chip muted">No inspirations</span>'
    else:
        insp_html = "\n".join(
            f'<span class="semantic-chip">{i["concept"]}</span>'
            for i in insp
        )

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



print("\n===== DEBUG NODES (SAMPLE) =====")

print("NODE COUNT:", len(nodes))
print("EDGE COUNT:", len(edges))

# show structure of first node
if nodes:
    first_key = next(iter(nodes))
    print("\nFIRST NODE KEY:", first_key)
    print("FIRST NODE VALUE:")
    print(json.dumps(nodes[first_key], indent=2)[:2000])

print("\nFIRST 5 EDGES:")
for e in edges[:5]:
    print(e)

print("\n===== END DEBUG =====\n")
    

    
print()
print("===== HOMEPAGE DEBUG =====")

print("NODE COUNT:", len(nodes))
print("EDGE COUNT:", len(edges))

print()
print("FIRST 10 NODE KEYS:")

for i, k in enumerate(nodes.keys()):
    if i >= 10:
        break
        print(" ", k)

print()
print("FIRST 5 NODE OBJECTS:")

for i, (k, v) in enumerate(nodes.items()):
    if i >= 5:
        break

    print()
    print("NODE:", k)

    if isinstance(v, dict):
        print("KEYS:", list(v.keys()))

        if "title" in v:
            print("TITLE:", v["title"])

        if "url" in v:
            print("URL:", v["url"])

        if "concepts" in v:
            print("CONCEPTS:", v["concepts"][:10])

print()
print("FIRST 10 EDGES:")

for e in edges[:10]:
    print(e)

print()
print("===== END DEBUG =====")
    
built = build(nodes, edges)

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
