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
# SALIENCE-NATIVE RELATION ENGINE
# (no precomputed "related" allowed)
# =========================================================

def compute_related(url, limit=5):

    # map: concept → salience
    concept_weights = {}

    for concept, node in salience.items():
        concept_weights[concept] = node.get("salience", 0)

    # find all concepts this page belongs to
    page_concepts = set()

    for concept, node in salience.items():
        pages = node.get("pages", [])

        if any(p["url"] == url for p in pages):
            page_concepts.add(concept)

    if not page_concepts:
        return []

    # score other pages
    scores = {}

    for concept in page_concepts:
        node = salience.get(concept, {})
        pages = node.get("pages", [])

        weight = concept_weights.get(concept, 0)

        for p in pages:
            other_url = p["url"]

            if other_url == url:
                continue

            scores[other_url] = scores.get(other_url, 0) + weight

    # rank
    ranked = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [url for url, _ in ranked[:limit]]


# =========================================================
# PLUGIN SYSTEM
# =========================================================

def run_plugin(name, fn, soup, url):
    try:
        fn(soup, url)
    except Exception as e:
        print(f"⚠️ Plugin failed [{name}] -> {e}")


# =========================================================
# PLUGINS (SALIENCE-ONLY CONTRACT)
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
    heading.string = "Further paths to ponder…"
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
    # reserved expansion hook (pure salience future layer)
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
# ENGINE CORE (SALIENCE-ONLY MODE)
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

    print("✅ Plugin registry enhancement complete")


if __name__ == "__main__":
    main()
