import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
CLUSTERS_FILE = os.path.join(ROOT, "concept-clusters.json")
OUTPUT = os.path.join(ROOT, "semantic-salience.json")


# =========================================================
# LOAD DATA
# =========================================================

with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f)["edges"]

with open(CLUSTERS_FILE, "r", encoding="utf-8") as f:
    clusters = json.load(f)


# =========================================================
# DIRECTIONAL WEIGHT MODEL
# =========================================================

inflow = defaultdict(float)
outflow = defaultdict(float)

for edge in graph:
    w = edge.get("weight", 1)

    src = edge["from"]
    dst = edge["to"]

    # outgoing pressure (projection)
    outflow[src] += w

    # incoming pressure (absorption)
    inflow[dst] += w


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(d):
    max_v = max(d.values(), default=1)
    return {k: round(v / max_v, 4) for k, v in d.items()}


inflow = normalize(inflow)
outflow = normalize(outflow)


# =========================================================
# COMPOSITE SALIENCE FIELDS
# =========================================================

output = {}

for concept, pages in clusters.items():

    i = inflow.get(concept, 0.0)
    o = outflow.get(concept, 0.0)

    # core idea:
    # - inflow = "how much the world feeds this concept"
    # - outflow = "how much this concept distributes meaning"

    stability = 1 - abs(i - o)

    output[concept] = {
        "inflow": i,
        "outflow": o,
        "stability": round(stability, 4),
        "salience": round((i + o) / 2, 4),
        "page_count": len(pages),
        "pages": pages
    }


# =========================================================
# SAVE
# =========================================================

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("🧠 Directional semantic salience built")
print("📦 Wrote:", OUTPUT)
