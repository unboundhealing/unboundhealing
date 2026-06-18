import json
from collections import defaultdict

INPUT = "semantic-model.json"
OUTPUT = "concept-clusters.json"

with open(INPUT, "r", encoding="utf-8") as f:
    pages = json.load(f)

clusters = defaultdict(list)

for url, data in pages.items():

    concepts = data.get("concepts", [])

    # top 5 concepts only
    for concept in concepts[:5]:
        clusters[concept].append({
            "url": url,
            "title": data.get("title", "")
        })

# remove weak clusters
result = {}

for concept, members in clusters.items():
    if len(members) >= 2:
        result[concept] = sorted(
            members,
            key=lambda x: x["title"]
        )

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print("🧩 Concept clusters built (v3.3)")
