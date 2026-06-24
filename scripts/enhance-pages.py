import json
import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict

# =========================================================
# ROOT + TRUTH LAYER
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")

TRACKER_PATH = "/assets/js/semantic-tracker.js"


# =========================================================
# LOAD SINGLE TRUTH LAYER (HARD GUARANTEE)
# =========================================================

def load_salience():
    if not os.path.exists(SALIENCE_FILE):
        raise FileNotFoundError(
            "❌ semantic-salience.json missing (REQUIRED SINGLE TRUTH LAYER)"
        )

    with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("❌ semantic-salience must be a dict")

    return data


salience = load_salience()


# =========================================================
# FILE DISCOVERY (consumer-safe)
# =========================================================

def find_html_files():
    html_files = []

    for root_dir, _, files in os.walk(ROOT):
        normalized = root_dir.replace("\\", "/")

        # avoid assets + generated noise
        if "/assets/" in normalized:
            continue

        for file_name in files:
            if file_name.endswith(".html"):
                html_files.append(os.path.join(root_dir, file_name))

    return html_files


# =========================================================
# URL NORMALIZATION (canonical form)
# =========================================================

def get_url_from_file(file_path):
    rel = os.path.relpath(file_path, ROOT).replace("\\", "/")

    rel = rel.replace("index.html", "")
    rel = rel.replace(".html", "")

    rel = rel.strip("/")

    return f"https://unboundhealing.org/{rel}" if rel else "https://unboundhealing.org/"


def fallback_title(url):
    path = url.replace("https://unboundhealing.org", "").strip("/")
    if not path:
        return "Home"

    slug = path.split("/")[-1]
    return slug.replace("-", " ").title()


# =========================================================
# SAFE SALIENCE ACCESSORS
# =========================================================

def safe_node(node):
    return node if isinstance(node, dict) else {}


def get_concepts(node):
    node = safe_node(node)
    concepts = node.get("concepts", [])
    return concepts if isinstance(concepts, list) else []


def get_concept_weight_map(node):
    """
    Build concept → weight map from salience node.
    If weight missing, default to 1.0.
    """
    node = safe_node(node)
    concepts = get_concepts(node)

    weights = {}

    for c in concepts:
        if isinstance(c, dict):
            word = c.get("word")
            weight = c.get("weight", 1.0)

            if word:
                weights[word] = float(weight)

    return weights


# =========================================================
# CONCEPT INDEX (pure salience projection)
# =========================================================

def build_concept_index():
    index = defaultdict(list)

    for url, node in salience.items():
        for concept in get_concepts(node):
            if isinstance(concept, dict) and concept.get("word"):
                index[concept["word"]].append(url)

    return index


CONCEPT_INDEX = build_concept_index()


# =========================================================
# RELATED CONTENT ENGINE (SALIENCE-WEIGHTED)
# =========================================================

def compute_related(url, limit=5):
    node = safe_node(salience.get(url))

    concept_weights = get_concept_weight_map(node)

    if not concept_weights:
        return []

    scores = defaultdict(float)

    # weighted resonance propagation
    for concept, weight in concept_weights.items():
        related_pages = CONCEPT_INDEX.get(concept, [])

        for other_url in related_pages:
            if other_url == url:
                continue

            # salience-weighted contribution
            scores[other_url] += weight

    # rank by strongest semantic resonance
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))

    return [u for u, _ in ranked[:limit]]


# =========================================================
# PLUGIN SYSTEM (pure consumer layer)
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
    # remove old state (idempotent consumer behavior)
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
        href = r.replace("https://unboundhealing.org", "")
        a = soup.new_tag("a", href=href)
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
    # idempotent injection
    if soup.find("script", {"src": TRACKER_PATH}):
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True

    if soup.body:
        soup.body.append(script)
    else:
        soup.append(script)


def plugin_future_magic(soup, url):
    # intentionally inert consumer placeholder
    return


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
# PAGE ENHANCEMENT CORE
# =========================================================

def enhance_page(soup, url):
    for name in ACTIVE_PLUGINS:
        plugin = PLUGIN_REGISTRY.get(name)
        if plugin:
            run_plugin(name, plugin, soup, url)

    return soup


# =========================================================
# PROCESS FILE
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

    print("✅ Semantic gravity enhancement complete (salience-consumer only)")


if __name__ == "__main__":
    main()
