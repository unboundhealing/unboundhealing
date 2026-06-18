import json
from itertools import combinations

INPUT = "semantic-model.json"
OUTPUT = "semantic-graph.json"

with open(INPUT, "r", encoding="utf-8") as f:
    pages = json.load(f)

urls = list(pages.keys())

graph = {
    "nodes": [],
    "edges": []
}

for url, data in pages.items():
    graph["nodes"].append({
        "url": url,
        "title": data["title"],
        "tone": data["tone"],
        "intent": data["intent"]
    })

for a, b in combinations(urls, 2):

    concepts_a = set(pages[a]["concepts"])
    concepts_b = set(pages[b]["concepts"])

    overlap = concepts_a.intersection(concepts_b)

    if not overlap:
        continue

    score = len(overlap)

    graph["edges"].append({
        "from": a,
        "to": b,
        "weight": score,
        "shared_concepts": sorted(list(overlap))
    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(graph, f, indent=2)

print("🧭 Semantic graph built (v3.3)")
