import json
import os
from bs4 import BeautifulSoup
from collections import defaultdict

# =========================================================
# ROOT + TRUTH LAYER
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")

TRACKER_PATH = "/assets/js/semantic-tracker.js"
HOME_INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")


# =========================================================
# LOAD TRUTH LAYER (STRICT)
# =========================================================

def load_salience():
    if not os.path.exists(SALIENCE_FILE):
        raise FileNotFoundError("❌ semantic-salience.json missing")

    with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("❌ semantic-salience must be dict")

    return data


salience = load_salience()


# =========================================================
# FILE DISCOVERY
# =========================================================

def find_html_files():
    html_files = []

    for root_dir, _, files in os.walk(ROOT):
        normalized = root_dir.replace("\\", "/")

        if "/assets/" in normalized:
            continue

        for f in files:
            if not f.endswith(".html"):
                continue

            full = os.path.join(root_dir, f)
            full_norm = full.replace("\\", "/")

            if "/assets/" in full_norm:
                continue

            html_files.append(full)

    return html_files


# =========================================================
# URL NORMALIZATION
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
    return path.split("/")[-1].replace("-", " ").title()


# =========================================================
# SAFE ACCESSORS
# =========================================================

def safe_node(node):
    return node if isinstance(node, dict) else {}


def get_concepts(node):
    node = safe_node(node)
    c = node.get("concepts", [])
    return c if isinstance(c, list) else []


def get_concept_weight_map(node):
    node = safe_node(node)
    weights = {}

    for c in get_concepts(node):
        if isinstance(c, dict):
            word = c.get("word")
            w = c.get("weight", 1.0)
        elif isinstance(c, str):
            word = c
            w = 1.0
        else:
            continue

        if word:
            try:
                weights[word] = float(w)
            except Exception:
                weights[word] = 1.0

    return weights


# =========================================================
# LAZY CONCEPT INDEX
# =========================================================

_CONCEPT_INDEX = None

def build_concept_index():
    index = defaultdict(set)
    pages = salience.get("pages", salience)

    for url, node in pages.items():
        for c in get_concepts(node):
            if isinstance(c, dict):
                word = c.get("word")
            elif isinstance(c, str):
                word = c
            else:
                continue

            if word:
                index[word].add(url)

    return {k: list(v) for k, v in index.items()}


def get_concept_index():
    global _CONCEPT_INDEX
    if _CONCEPT_INDEX is None:
        _CONCEPT_INDEX = build_concept_index()
    return _CONCEPT_INDEX


# =========================================================
# RELATED CONTENT ENGINE
# =========================================================

def compute_related(url, limit=5):
    node = safe_node(salience.get(url))

    weights = get_concept_weight_map(node)
    if not weights:
        return []

    index = get_concept_index()

    scores = defaultdict(float)

    for concept, weight in weights.items():
        for other in set(index.get(concept, [])):
            if other != url:
                scores[other] += weight

    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    return [u for u, _ in ranked[:limit]]


# =========================================================
# PLUGIN SYSTEM
# =========================================================

def run_plugin(name, fn, soup, url):
    print(f"🔌 plugin: {name} → {url}")
    try:
        fn(soup, url)
    except Exception as e:
        print(f"⚠️ plugin failed [{name}]: {e}")


# =========================================================
# PLUGINS
# =========================================================

def plugin_related_content(soup, url):
    for old in soup.select("section.related-paths"):
        old.decompose()

    related = compute_related(url)
    if not related:
        return

    block = soup.new_tag("section")
    block["class"] = "related-paths"

    h = soup.new_tag("h3")
    h.string = "Further paths to follow..."
    block.append(h)

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
    """
    FUTURE MAGIC (PLACEHOLDER HOOK)

    Purpose:
    - reserved insertion point for future features
    - intentionally does nothing semantically
    - safe non-interrupting DOM marker
    """

    root = soup.body if soup.body else soup

    block = soup.new_tag("div")
    block["class"] = "future-magic"

    # very light, non-intrusive marker
    note = soup.new_tag("p")
    note.string = "future_magic goes here"
    block.append(note)

    root.append(block)


# =========================================================
# HOMEPAGE INTELLIGENCE (INJECTOR)
# =========================================================

def load_homepage_intelligence():
    if not os.path.exists(HOME_INTEL_FILE):
        return None

    try:
        with open(HOME_INTEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def inject_homepage_intelligence(soup, url):
    """
    Renders:
    - Arising observations
    - Essential inspirations
    Only if homepage intelligence exists.
    """

    data = load_homepage_intelligence()
    if not data:
        return

    # prevent duplicates
    for old in soup.select("section.homepage-intelligence"):
        old.decompose()

    root = soup.new_tag("section")
    root["class"] = "homepage-intelligence"

    # -------------------------
    # TOP CONCEPTS → Essential inspirations
    # -------------------------
    concepts = data.get("homepage_intelligence", {}).get("top_concepts", [])[:3]

    if concepts:
        sec = soup.new_tag("div")
        sec["class"] = "essential-inspirations"

        h = soup.new_tag("h2")
        h.string = "Essential inspirations"
        sec.append(h)

        cloud = soup.new_tag("div")
        cloud["class"] = "chip-cloud"

        for c in concepts:
            a = soup.new_tag("a", href="#")
            a["class"] = "chip"
            a.string = c.get("concept", "...")
            cloud.append(a)

        sec.append(cloud)
        root.append(sec)

    # -------------------------
    # TOP HUBS → Arising observations
    # -------------------------
    hubs = data.get("homepage_intelligence", {}).get("top_hubs", [])[:3]

    if hubs:
        sec = soup.new_tag("div")
        sec["class"] = "arising-observations"

        h = soup.new_tag("h2")
        h.string = "Arising observations"
        sec.append(h)

        cloud = soup.new_tag("div")
        cloud["class"] = "chip-cloud"

        for hnode in hubs:
            a = soup.new_tag("a", href="#")
            a["class"] = "chip"
            a.string = fallback_title(hnode.get("node", ""))
            cloud.append(a)

        sec.append(cloud)
        root.append(sec)

    if soup.body:
        soup.body.append(root)
    else:
        soup.append(root)


# =========================================================
# PLUGIN REGISTRY
# =========================================================

PLUGIN_REGISTRY = {
    "related_content": plugin_related_content,
    "tracking": plugin_tracking,
    "homepage_intelligence": inject_homepage_intelligence,
    "future_magic": plugin_future_magic,
}

ACTIVE_PLUGINS = [
    "related_content",
    "tracking",
    "homepage_intelligence",
    "future_magic",
]


# =========================================================
# PAGE ENHANCEMENT CORE
# =========================================================

def enhance_page(soup, url):
    for name in ACTIVE_PLUGINS:
        fn = PLUGIN_REGISTRY.get(name)
        if fn:
            run_plugin(name, fn, soup, url)

    return soup


# =========================================================
# PROCESS FILE
# =========================================================

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            soup = BeautifulSoup(f, "lxml")
        except Exception:
            soup = BeautifulSoup(f, "html.parser")

    url = get_url_from_file(file_path)
    enhance_page(soup, url)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


# =========================================================
# ENTRYPOINT
# =========================================================

def main():
    files = find_html_files()

    for f in files:
        try:
            process_file(f)
            print(f"✨ Enhanced {f}")
        except Exception as e:
            print(f"⚠️ Skipped {f}: {e}")

    print("✅ Semantic gravity enhancement complete")


if __name__ == "__main__":
    main()
