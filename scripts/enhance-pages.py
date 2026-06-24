import json
import os
from bs4 import BeautifulSoup
from collections import defaultdict

# =========================================================
# ROOT + SINGLE TRUTH LAYER
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")

TRACKER_PATH = "/assets/js/semantic-tracker.js"


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
            if f.endswith(".html"):
                full = os.path.join(root_dir, f)
                full_norm = full.replace("\\", "/")

                if "/assets/" in full_norm:
                    continue

                html_files.append(full)

    return html_files


# =========================================================
# URL HELPERS
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
# SAFE ACCESS
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
# SINGLE SALIENCE QUERY ENGINE (NEW CORE ABSTRACTION)
# =========================================================

def query_salience(url, mode="related", limit=5):
    """
    Single truth-layer interface.

    mode:
      - "related": graph adjacency-style relevance
      - "homepage": salience-weighted global importance
    """

    node = safe_node(salience.get(url))

    if mode == "related":
        weights = get_concept_weight_map(node)
        if not weights:
            return []

        index = salience.get("_concept_index")
        if index is None:
            index = build_concept_index()

        scores = defaultdict(float)

        for concept, weight in weights.items():
            for other in set(index.get(concept, [])):
                if other != url:
                    scores[other] += weight

        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return [u for u, _ in ranked[:limit]]

    if mode == "homepage":
        pages = salience.get("pages", salience)

        scored = []
        for u, n in pages.items():
            if u == url:
                continue

            w = 0.0
            for c in get_concepts(n):
                if isinstance(c, dict):
                    w += float(c.get("weight", 1.0))
                else:
                    w += 1.0

            scored.append((u, w))

        scored.sort(key=lambda x: (-x[1], x[0]))
        return [u for u, _ in scored[:limit]]

    return []


# =========================================================
# PLUGIN CORE
# =========================================================

def run_plugin(name, fn, soup, url):
    print(f"🔌 plugin: {name} → {url}")
    try:
        fn(soup, url)
    except Exception as e:
        print(f"⚠️ plugin failed [{name}]: {e}")


# =========================================================
# PLUGINS (NOW PURE CONSUMERS OF SALIENCE)
# =========================================================

def plugin_related_content(soup, url):
    for old in soup.select("section.related-paths"):
        old.decompose()

    related = query_salience(url, mode="related")
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

    if soup.body:
        soup.body.append(block)
    else:
        soup.append(block)


def plugin_tracking(soup, url):
    if soup.find("script", {"src": TRACKER_PATH}):
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True

    if soup.body:
        soup.body.append(script)
    else:
        soup.append(script)


def plugin_homepage_intelligence(soup, url):
    for old in soup.select("section.homepage-intelligence"):
        old.decompose()

    top_nodes = query_salience(url, mode="homepage", limit=3)
    if not top_nodes:
        return

    root = soup.new_tag("section")
    root["class"] = "homepage-intelligence"

    h = soup.new_tag("h2")
    h.string = "Homepage intelligence"
    root.append(h)

    cloud = soup.new_tag("div")
    cloud["class"] = "chip-cloud"

    for node_url in top_nodes:
        a = soup.new_tag("a", href=node_url.replace("https://unboundhealing.org", ""))
        a["class"] = "chip"
        a.string = fallback_title(node_url)
        cloud.append(a)

    root.append(cloud)

    if soup.body:
        soup.body.append(root)
    else:
        soup.append(root)


def plugin_future_magic(soup, url):
    comment = soup.new_string("<!-- future_magic hook active -->")

    if soup.body:
        soup.body.append(comment)
    else:
        soup.append(comment)


# =========================================================
# PLUGIN REGISTRY (DETERMINISTIC ORDER)
# =========================================================

PLUGIN_REGISTRY = {
    "related_content": plugin_related_content,
    "tracking": plugin_tracking,
    "homepage_intelligence": plugin_homepage_intelligence,
    "future_magic": plugin_future_magic,
}

PLUGIN_ORDER = [
    "related_content",
    "tracking",
    "homepage_intelligence",
    "future_magic",
]

ACTIVE_PLUGINS = PLUGIN_ORDER


# =========================================================
# PIPELINE
# =========================================================

def enhance_page(soup, url):
    for name in ACTIVE_PLUGINS:
        fn = PLUGIN_REGISTRY.get(name)
        if fn:
            run_plugin(name, fn, soup, url)

    return soup


# =========================================================
# FILE PROCESSOR
# =========================================================

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

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

    print("✅ Semantic-salience consumer layer complete (single truth architecture intact)")


if __name__ == "__main__":
    main()
