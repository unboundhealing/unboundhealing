import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT_FILE = os.path.join(ROOT, "content-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-graph.json")

STOP = {"this","that","just","about","here","like","thing"}

def valid(c):
    return c and c.lower() not in STOP


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

edges_out = []

for e in raw.get("edges", []):

    concepts = [
        c.lower().strip()
        for c in e.get("shared_concepts", [])
        if valid(c)
    ]

    # remove ultra-noisy edges
    if len(concepts) < 1:
        continue

    # cap explosion
    concepts = concepts[:6]

    edges_out.append({
        "from": e["from"],
        "to": e["to"],
        "weight": min(float(e.get("weight", 1)), 5.0),
        "shared_concepts": concepts
    })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"edges": edges_out}, f, indent=2)

print("🧭 Semantic graph built (v4.0 denoised)")
print("📦 edges:", len(edges_out))
