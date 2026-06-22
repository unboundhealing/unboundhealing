import json

INPUT = "content-model.json"
OUTPUT = "content-graph.json"

with open(INPUT, "r", encoding="utf-8") as f:
    raw = json.load(f)

# -----------------------------
# NORMALIZE INPUT
# -----------------------------
pages = []

if isinstance(raw, dict):

    if "pages" in raw:
        pages = raw["pages"]

    else:
        for url, obj in raw.items():
            if not isinstance(obj, dict):
                continue

            tags = obj.get("tags", [])

            # FIX: normalize tag formats
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]

            pages.append({
                "url": url,
                "title": obj.get("title", ""),
                "tags": tags
            })

elif isinstance(raw, list):
    pages = raw

if not pages:
    print("❌ No pages detected after normalization")
    print("raw type:", type(raw))
    exit(1)

# -----------------------------
# DEBUG: TAG HEALTH
# -----------------------------
empty_tags = sum(1 for p in pages if not p.get("tags"))

print("\n🧪 TAG HEALTH")
print("pages:", len(pages))
print("pages with empty tags:", empty_tags)

nodes = []
edges = []

def overlap(a, b):
    return len(set(a) & set(b))

# -----------------------------
# BUILD GRAPH
# -----------------------------
for i, a in enumerate(pages):

    tags_a = a.get("tags", [])
    if isinstance(tags_a, str):
        tags_a = [t.strip() for t in tags_a.split(",") if t.strip()]

    nodes.append({
        "url": a.get("url"),
        "title": a.get("title", ""),
        "tags": tags_a
    })

    for j, b in enumerate(pages):
        if i >= j:
            continue

        tags_b = b.get("tags", [])
        if isinstance(tags_b, str):
            tags_b = [t.strip() for t in tags_b.split(",") if t.strip()]

        score = overlap(tags_a, tags_b)

        if score > 0:
            edges.append({
                "from": a.get("url"),
                "to": b.get("url"),
                "weight": float(score),
                "shared_concepts": list(set(tags_a) & set(tags_b))
            })

print("\n🔗 GRAPH STATS")
print("nodes:", len(nodes))
print("edges:", len(edges))

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({"nodes": nodes, "edges": edges}, f, indent=2, ensure_ascii=False)

print("✅ Content graph built (v3.5 normalized tags + stable projection)")
