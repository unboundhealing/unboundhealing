import json
import os
import re
from bs4 import BeautifulSoup

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")
PAGE_TITLES_FILE = os.path.join(ROOT, "page-titles.json")
TRACKER_PATH = "/assets/js/semantic-tracker.js"


# =========================================================
# LOAD SALIENCE (SINGLE SOURCE OF TRUTH)
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

def find_html_files():
    html_files = []

    for root_dir, _, files in os.walk(ROOT):
        if "/assets/" in root_dir.replace("\\", "/"):
            continue

        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root_dir, f))

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


def lookup_title(url):
    path = url.replace("https://unboundhealing.org", "").rstrip("/")
    key = "/" if path == "" else f"{path}/"

    if key in page_titles:
        return page_titles[key]

    slug = key.strip("/").split("/")[-1]
    return slug.replace("-", " ").title()


# =========================================================
# SALIENCE-ONLY RELATION ENGINE
# (pure projection: concept ↔ page bipartite scoring)
# =========================================================

def compute_related(url, limit=5):
    """
    Core idea:
    - salience = concept nodes
    - each concept contains pages
    - relatedness = sum of shared concept salience weights
    """

    # 1. build reverse index: page → concepts it belongs to
    page_to_concepts = {}

    for concept, node in salience.items():
        for p in node.get("pages", []):
            page_to_concepts.setdefault(p["url"], set()).add(concept)

    if url not in page_to_concepts:
        return []

    source_concepts = page_to_concepts[url]

    # 2. score pages by shared concept salience
    scores = {}

    for concept in source_concepts:
        node = salience.get(concept, {})
        weight = node.get("salience", 0)

        for p in node.get("pages", []):
            other = p["url"]

            if other == url:
                continue

            scores[other] = scores.get(other, 0) + weight

    # 3. rank deterministically
    ranked = sorted(
        scores.items(),
        key=lambda x: (-x[1], x[0])
    )

    return [u for u, _ in ranked[:limit]]


# =========================================================
# PLUGIN SYSTEM
# =========================================================

def run_plugin(name, fn, soup, url):
    try:
        fn(soup, url)
    except Exception as e:
        print(f"⚠️ Plugin failed [{name}] -> {e}")


# =========================================================
# PLUGINS (PURE SALIENCE CONTRACT)
# =========================================================

def plugin_related_content(soup, url):

    # idempotent cleanup
    for old in soup.select("section.related-paths"):
        old.decompose()

    related = compute_related(url)

    if not related:
        return

    block = soup.new_tag("section")
    block["class"] = "related-paths"

    heading = soup.new_tag("h3")
    heading.string = "Further paths to explore…"
    block.append(heading)

    cloud = soup.new_tag("div")
    cloud["class"] = "related-cloud"

    for related_url in related:
        a = soup.new_tag(
            "a",
            href=related_url.replace("https://unboundhealing.org", "")
        )
        a["class"] = "related-chip"
        a.string = lookup_title(related_url)
        cloud.append(a)

    block.append(cloud)

    footer = soup.find("footer")

    if footer:
        footer.insert_before(block)
    elif soup.body:
        soup.body.append(block)


def plugin_tracking(soup, url):

    if soup.find("script", {"src": TRACKER_PATH}):
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True

    if soup.body:
        soup.body.append(script)
    else:
        soup.append(script)


def plugin_future_magic(soup, url):
    # intentionally empty (reserved salience expansion layer)
    pass


# =========================================================
# REGISTRY
# =========================================================

PLUGIN_REGISTRY = {
    "related_content": plugin_related_content,
    "tracking": plugin_tracking,
    "future_magic": plugin_future_magic,
}

ACTIVE_PLUGINS = [
    "related_content",
    "tracking",
    "future_magic",
]


# =========================================================
# ENGINE CORE
# =========================================================

def enhance_page(soup, url):

    for name in ACTIVE_PLUGINS:
        plugin = PLUGIN_REGISTRY.get(name)

        if not plugin:
            print(f"⚠️ Unknown plugin: {name}")
            continue

        run_plugin(name, plugin, soup, url)

    return soup


# =========================================================
# PIPELINE
# =========================================================

def process_file(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    url = get_url_from_file(file_path)

    enhance_page(soup, url)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"✨ Enhanced {file_path}")


# =========================================================
# ENTRYPOINT
# =========================================================

def main():
    html_files = find_html_files()

    for file_path in html_files:
        try:
            process_file(file_path)
        except Exception as e:
            print(f"⚠️ Skipped {file_path}: {e}")

    print("✅ Semantic salience enhancement complete")


if __name__ == "__main__":
    main()
