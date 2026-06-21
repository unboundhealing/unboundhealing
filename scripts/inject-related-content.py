import json
import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "word-graph.json")
WORDS_FILE = os.path.join(ROOT, "semantic-words.json")
PAGE_TITLES_FILE = os.path.join(ROOT, "page-titles.json")

# -----------------------------
# Load data
# -----------------------------
CONCEPTS_FILE = os.path.join(ROOT, "semantic-concepts.json")

with open(CONCEPTS_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

concepts = data.get("nodes") or data.get("concepts") or data.get("items")
edges = data.get("edges")

if concepts is None:
    raise ValueError(f"Can't find concept list. Keys found: {list(data.keys())}")

if os.path.exists(PAGE_TITLES_FILE):
    with open(PAGE_TITLES_FILE, "r", encoding="utf-8") as f:
        page_titles = json.load(f)
else:
    page_titles = {}
    
# -----------------------------
# Build lookup tables
# -----------------------------
concept_to_urls = defaultdict(list)
url_to_concept = {}

for c in concepts:
    cid = c["id"]
    urls = c.get("urls", [])

    concept_to_urls[cid].extend(urls)

    for u in urls:
        url_to_concept[u] = cid

# -----------------------------
# Build adjacency map
# -----------------------------
adj = defaultdict(list)

for edge in edges:
    a = edge["from"]
    b = edge["to"]
    w = edge["weight"]

    adj[a].append((b, w))
    adj[b].append((a, w))

# -----------------------------
# Helpers
# -----------------------------
def find_html_files():
    html_files = []

    for root, _, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))

    return html_files


def get_url_from_file(file_path):
    rel = (
        file_path
        .replace(ROOT, "")
        .replace("index.html", "")
        .replace(".html", "")
    )

    rel = re.sub(r"^/", "", rel)

    return f"https://unboundhealing.org/{rel}"


def pick_related(word, current_url, limit=5):

    candidates = []

    for neighbor, weight in adj.get(word, []):

        for url in word_to_urls.get(neighbor, []):

            if url != current_url:
                candidates.append((url, weight))

    candidates.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return [c[0] for c in candidates[:limit]]


def lookup_title(url):

    path = (
        url.replace(
            "https://unboundhealing.org",
            ""
        )
        .rstrip("/")
    )

    if path == "":
        key = "/"
    else:
        key = f"{path}/"

    title = page_titles.get(key)

    if title:
        return title

    slug = key.strip("/").split("/")[-1]

    return concept_titles.get(slug) or slug.replace("-", " ").title()

# -----------------------------
# Injection logic
# -----------------------------
HTML_FILES = find_html_files()

for file in HTML_FILES:

    try:

        with open(file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # ----------------------------------
        # Remove previous injections
        # ----------------------------------
        for old in soup.select("section.related-paths"):
            old.decompose()

        url = get_url_from_file(file)

        if url not in url_to_concept:
            continue

        concept = url_to_concept[url]

        related = pick_related(concept, url, limit=5)

        if not related:
            continue

        # ----------------------------------
        # Create section
        # ----------------------------------
        block = soup.new_tag("section")
        block["class"] = "related-paths"

        heading = soup.new_tag("h3")
        heading.string = "Further paths to ponder…"

        block.append(heading)

        cloud = soup.new_tag("div")
        cloud["class"] = "related-cloud"

        for r in related:

            a = soup.new_tag(
                "a",
                href=r.replace(
                    "https://unboundhealing.org",
                    ""
                )
            )

            a["class"] = "related-chip"

            a.string = lookup_title(r)

            cloud.append(a)

        block.append(cloud)

        # ----------------------------------
        # Insert before footer if present
        # ----------------------------------
        footer = soup.find("footer")

        if footer:
            footer.insert_before(block)

        elif soup.body:
            soup.body.append(block)

        with open(file, "w", encoding="utf-8") as f:
            f.write(str(soup))

        print(f"🔗 Injected related paths into {file}")

    except Exception as e:

        print(f"⚠️ Skipped {file}: {e}")

print("✅ Phase 3 injection complete")
