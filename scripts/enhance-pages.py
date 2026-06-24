import json
import os
import re
from bs4 import BeautifulSoup

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")

TRACKER_PATH = "/assets/js/semantic-tracker.js"

# =========================================================
# LOAD SINGLE TRUTH LAYER (HARD REQUIREMENT)
# =========================================================

def load_salience():
    if not os.path.exists(SALIENCE_FILE):
        raise FileNotFoundError("❌ semantic-salience.json missing (REQUIRED TRUTH LAYER)")

    with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


salience = load_salience()

# =========================================================
# FILE DISCOVERY
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


# =========================================================
# URL MAPPING
# =========================================================

def get_url_from_file(file_path):
    rel = file_path.replace(ROOT, "")

    rel = rel.replace("index.html", "")
    rel = rel.replace(".html", "")

    rel = re.sub(r"^/", "", rel)

    return f"https://unboundhealing.org/{rel}"


def fallback_title(url):
    path = url.replace("https://unboundhealing.org", "").rstrip("/")
    slug = path.split("/")[-1] if path else "home"
    return slug.replace("-", " ").title() or "Home"


# =========================================================
# SAFE ACCESSORS
# =========================================================

def safe_node(node):
    return node if isinstance(node, dict) else {}


def get_concepts(node):
    node = safe_node(node)
    c = node.get("concepts", [])
    return c if isinstance(c, list) else []


# =========================================================
# CONCEPT INDEX (FROM SINGLE TRUTH LAYER)
# =========================================================

def build_concept_index():
    index = {}

    for url, node in salience.items():
        node = safe_node(node)

        for concept in get_concepts(node):
            index.setdefault(concept, []).append(url)

    return index


CONCEPT_INDEX = build_concept_index()


# =========================================================
# RELATED CONTENT ENGINE (TRUTH LAYER ONLY)
# =========================================================

def compute_related(url, limit=5):
    node = safe_node(salience.get(url))

    concepts = get_concepts(node)

    if not concepts:
        return []

    scores = {}

    for concept in concepts:
        for other in CONCEPT_INDEX.get(concept, []):
            if other == url:
                continue
            scores[other] = scores.get(other, 0) + 1

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
    # remove old blocks
    for old in soup.select("section.related-paths"):
        old.decompose()

    related = compute_related(url)

    if not related:
        return

    block = soup.new_tag("section")
    block["class"] = "related-paths"

    heading = soup.new_tag("h3")
    heading.string = "Nearby paths..."
    block.append(heading)

    cloud = soup.new_tag("div")
    cloud["class"] = "related-cloud"

    for r in related:
        a = soup.new_tag("a", href=r.replace("https://unboundhealing.org", ""))
        a["class"] = "related-chip"
        a.string = fallback_title(r)
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
# CORE PIPELINE
# =========================================================

def enhance_page(soup, url):
    for name in ACTIVE_PLUGINS:
        plugin = PLUGIN_REGISTRY.get(name)
        if plugin:
            run_plugin(name, plugin, soup, url)
    return soup


# =========================================================
# PROCESSING
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

    for f in html_files:
        try:
            process_file(f)
        except Exception as e:
            print(f"⚠️ Skipped {f}: {e}")

    print("✅ Semantic gravity enhancement complete (truth-layer consumer only)")


if __name__ == "__main__":
    main()
