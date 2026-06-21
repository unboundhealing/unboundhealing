import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")
PAGE_TITLES_FILE = os.path.join(ROOT, "page-titles.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-context.json")

# -----------------------------
# Load inputs
# -----------------------------
with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
    salience = json.load(f)

if os.path.exists(PAGE_TITLES_FILE):
    with open(PAGE_TITLES_FILE, "r", encoding="utf-8") as f:
        page_titles = json.load(f)
else:
    page_titles = {}

# -----------------------------
# Helpers
# -----------------------------
def lookup_title(url):
    path = url.replace("https://unboundhealing.org", "").rstrip("/")
    key = "/" if path == "" else f"{path}/"

    if key in page_titles:
        return page_titles[key]

    slug = key.strip("/").split("/")[-1]
    return slug.replace("-", " ").title()


def build_related(items, current_url, limit=5):
    if not items:
        return []

    related = []
    for r in items:
        if r["url"] == current_url:
            continue

        related.append({
            "url": r["url"],
            "score": r.get("score", 0)
        })

    related.sort(key=lambda x: x["score"], reverse=True)
    return related[:limit]

# -----------------------------
# Build context map
# -----------------------------
context = {}

for url, data in salience.items():

    related_items = data.get("related", [])

    context[url] = {
        "url": url,
        "title": lookup_title(url),
        "related": build_related(related_items, url, limit=5),
        "raw_salience": data.get("salience", 0),
        "page_count": data.get("page_count", 0)
    }

# -----------------------------
# Write output
# -----------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(context, f, indent=2)

print(f"✅ Semantic context built → {OUTPUT_FILE}")
