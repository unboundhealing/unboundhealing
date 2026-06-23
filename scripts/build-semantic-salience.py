import json
import os
import math
import re
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT = os.path.join(ROOT, "content-model.json")
OUTPUT = os.path.join(ROOT, "semantic-salience.json")
DEBUG_GRAPH = os.path.join(ROOT, "semantic-graph-debug.json")

# =========================================================
# LOAD
# =========================================================

try:
    data = json.load(open(INPUT, "r", encoding="utf-8"))
except Exception:
    data = {"pages": []}

pages = data.get("pages", [])

# =========================================================
# NORMALIZATION (ABSOLUTE CONTRACT)
# =========================================================

def norm_id(x):
    if not x:
        return None

    x = str(x).strip()

    # remove broken prefix artifacts
    x = x.lstrip("|")

    # normalize url if present
    x = re.sub(r"^https?://[^/]+", "", x)

    x = "/" + x.strip("/")

    x = re.sub(r"/+", "/", x)

    return x.lower()

# =========================================================
# BUILD INTERNAL REPRESENTATION
# =========================================================

nodes = {}
edges = []

for p in pages:
    node_id = norm_id(p.get("id") or p.get("url") or p.get("file"))

    if not node_id:
        continue

    tags = [
        str(t).strip().lower()
        for t in (p.get("tags") or [])
        if t
    ]

    nodes[node_id] = {
        "id": node_id,
        "tags": tags
    }

node_list = list(nodes.values())

# =========================================================
# SAFE EDGE GENERATION (NO EXTERNAL GRAPH DEPENDENCY)
# =========================================================

for i, a in enumerate(node_list):
    for j, b in enumerate(node_list):

        if i == j:
            continue

        shared = list(set(a["tags"]) & set(b["tags"]))

        if not shared:
            continue

        edges.append({
            "from": a["id"],
            "to": b["id"],
            "weight": float(len(shared)),
            "shared": shared
        })

# =========================================================
# GRAVITY COMPUTATION (SELF-CONTAINED)
# =========================================================

inflow = defaultdict(float)
outflow = defaultdict(float)
connectivity = defaultdict(float)

for e in edges:
    w = e["weight"]
    inflow[e["to"]] += w
    outflow[e["from"]] += w

    connectivity[e["from"]] += 1
    connectivity[e["to"]] += 1

def clamp(x):
    return max(0.0, min(1.0, x))

# =========================================================
# FINAL SALIENCE (ONLY TRUTH LAYER)
# =========================================================

salience = {}

all_nodes = set(nodes.keys()) | set(inflow.keys()) | set(outflow.keys())

for n in all_nodes:

    i = inflow.get(n, 0.0)
    o = outflow.get(n, 0.0)
    c = connectivity.get(n, 0.0)

    s = (i + o) / 2.0
    conn = math.log1p(c)

    gravity = (s * 0.6) + (conn * 0.4)

    salience[n] = {
        "gravity": round(clamp(gravity / 5.0), 5),
        "salience": round(s, 5),
        "inflow": round(i, 5),
        "outflow": round(o, 5),
        "connectivity": round(conn, 5)
    }

# =========================================================
# WRITE OUTPUT (TRUTH LAYER)
# =========================================================

json.dump(salience, open(OUTPUT, "w", encoding="utf-8"), indent=2)

# =========================================================
# OPTIONAL DEBUG GRAPH (NON-CRITICAL)
# =========================================================

json.dump({
    "nodes": list(nodes.values()),
    "edges": edges
}, open(DEBUG_GRAPH, "w", encoding="utf-8"), indent=2)

# =========================================================
# SAFE EXIT (NEVER FAIL CI)
# =========================================================

print("✅ semantic-salience (truth layer) built")
print("📦 nodes:", len(nodes))
print("📦 edges:", len(edges))
