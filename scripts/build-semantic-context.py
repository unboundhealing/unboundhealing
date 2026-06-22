import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")
PAGE_TITLES_FILE = os.path.join(ROOT, "page-titles.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-context.json")


# =========================================================
# LOAD DATA
# =========================================================

with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
    salience = json.load(f)

if os.path.exists(PAGE_TITLES_FILE):
    with open(PAGE_TITLES_FILE, "r", encoding="utf-8") as f:
        page_titles = json.load(f)
else:
    page_titles = {}


# =========================================================
# HELPERS
# =========================================================

def lookup_title(url):
    path = url.replace("https://unboundhealing.org", "").rstrip("/")
    key = "/" if path == "" else f"{path}/"

    return page_titles.get(key)


def extract_related(node, url):
    if not node:
        return []

    return [
        item["url"]
        for item in node.get("related", [])
        if item.get("url") and item.get("url") != url
    ][:5]


# =========================================================
# BUILD CONTEXT MAP
# =========================================================

semantic_context = {}

for url, node in salience.items():

    semantic_context[url] = {
        "url": url,
        "title": lookup_title(url) or url,
        "related": extract_related(node, url),
        "salience_score": node.get("salience", 0),
        "page_count": node.get("page_count", 0),
    }


# =========================================================
# WRITE OUTPUT
# =========================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(semantic_context, f, indent=2)

for k, v in list(output.items())[:3]:
    print(k)
    print(v)
    print("---")

print(f"🧠 semantic-context.json built → {OUTPUT_FILE}")
print(f"📦 total nodes: {len(semantic_context)}")
print("CONTEXT SAMPLE:")

