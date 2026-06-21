import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")
OUTPUT = os.path.join(ROOT, "homepage-intelligence.json")

# -----------------------------
# Load data
# -----------------------------
def safe_load(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

salience_data = safe_load(SALIENCE_FILE)

print("SALIENCE SAMPLE:")
for k, v in list(salience_data.items())[:3]:
    print(k)
    print(v)
    print("---")
    

# -----------------------------
# Minimal stop filter (ONLY hygiene, not logic)
# -----------------------------
STOP = {
    "that", "this", "these", "those",
    "and", "or", "but",
    "the", "a", "an",
    "to", "of", "in", "on", "for",
    "unbound"
}

def is_noise(word: str) -> bool:
    w = word.strip().lower()
    return w in STOP or len(w) < 3


def normalize(word: str) -> str:
    return word.strip().lower()


# -----------------------------
# STEP 1 — extract concepts from salience
# -----------------------------
concepts = []

for concept, data in salience_data.items():

    name = normalize(concept)

    if is_noise(name):
        continue

    concepts.append({
        "concept": name,
        "salience": data.get("salience", 0),
        "page_count": data.get("page_count", 0),
        "pages": data.get("pages", [])
    })


# -----------------------------
# STEP 2 — sort by salience (single authority source)
# -----------------------------
concepts.sort(key=lambda x: x["salience"], reverse=True)


# -----------------------------
# STEP 3 — featured pages (light extraction only)
# -----------------------------
# derive featured pages from concept pages (no graph logic here)
page_scores = {}

for c in concepts:
    for p in c["pages"]:

        if isinstance(p, dict):
            url = p.get("url")
        else:
            url = p

        if not url:
            continue

        page_scores[url] = (
            page_scores.get(url, 0)
            + c["salience"]
        )
featured_pages = [
    {"url": url, "score": score}
    for url, score in sorted(
        page_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
]


# -----------------------------
# STEP 4 — select top concepts
# -----------------------------
top_concepts = [
    {
        "concept": c["concept"],
        "salience": c["salience"],
        "page_count": c["page_count"]
    }
    for c in concepts[:3]
]


# -----------------------------
# OUTPUT
# -----------------------------
output = {
    "featured_pages": featured_pages[:3],
    "concept_clusters": top_concepts
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("🏠 Homepage intelligence built (v3.5 unified salience pipeline)")
print("📦 Wrote:", OUTPUT)
