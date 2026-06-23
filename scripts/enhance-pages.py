import json
import os
import re
from bs4 import BeautifulSoup

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")
CONTEXT_FILE = os.path.join(ROOT, "semantic-context.json")
PAGE_TITLES_FILE = os.path.join(ROOT, "page-titles.json")

TRACKER_PATH = "/assets/js/semantic-tracker.js"


# =========================================================
# LOAD DATA (SAFE MODE)
# =========================================================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


salience = load_json(SALIENCE_FILE, {})
context = load_json(CONTEXT_FILE, {})
page_titles = load_json(PAGE_TITLES_FILE, {})


# =========================================================
# HELPERS
# =========================================================

def find_html_files():
    html_files = []

    for root_dir, _, files in os.walk(ROOT):
        if "/assets/" in root_dir.replace("\\", "/"):
            continue

        for file_name in files:
            if file_name.endswith(".html"):
                html_files.append(os.path.join(root_dir, file_name))

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
# SAFE NORMALIZER (CRITICAL FIX)
# =========================================================

def safe_node(node):
    """
    Ensures every salience entry behaves like a dict.
    Prevents list/object mismatch crashes.
    """
    if isinstance(node, dict):
        return node

    # if it's malformed (list, string, etc.)
    return {}


def get_concepts(node):
    node = safe_node(node)
    concepts = node.get("concepts", [])
    return concepts if isinstance(concepts, list) else []


# =========================================================
# BUILD CONCEPT INDEX (FIXED)
# =========================================================

def build_concept_index():
    concept_map = {}

    for url, node in salience.items():

        node = safe_node(node)

        for concept in get_concepts(node):
            concept_map.setdefault(concept, []).append(url)

    return concept_map


CONCEPT_MAP = build_concept_index()


# =========================================================
# RELATED ENGINE (TRUTH-LAYER ONLY)
# =========================================================

def compute_related(url, limit=3):

    if url not in salience:
        return []

    concepts = get_concepts(salience.get(url, {}))

    if not concepts:
        return []

    scores = {}

    for concept in concepts:

        for other_url in CONCEPT_MAP.get(concept, []):

            if other_url == url:
                continue

            scores[other_url] = scores.get(other_url, 0) + 1

    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))

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
# PLUGINS
# =========================================================

def plugin_related_content(soup, url):

    for old in soup.select("section.related-paths"):
        old.decompose()

    related = compute_related(url, limit=5)

    if not related:
        return

    block = soup.new_tag("section")
    block["class"] = "related-paths"

    heading = soup.new_tag("h3")
    heading.string = "Nearby paths..."
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
# CORE
# =========================================================

def enhance_page(soup, url):

    for name in ACTIVE_PLUGINS:
        plugin = PLUGIN_REGISTRY.get(name)
        if plugin:
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

    print("✅ Semantic gravity enhancement complete")


if __name__ == "__main__":
    main()
