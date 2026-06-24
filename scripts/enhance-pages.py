import json
import os
from bs4 import BeautifulSoup

# =========================================================
# ROOT + SINGLE TRUTH LAYER
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")

TRACKER_PATH = "/assets/js/semantic-tracker.js"


# =========================================================
# LOAD TRUTH LAYER (NO DERIVATION, NO TRANSFORMS)
# =========================================================

def load_salience():
    if not os.path.exists(SALIENCE_FILE):
        raise FileNotFoundError("❌ semantic-salience.json missing")

    with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("❌ semantic-salience must be dict")

    return data


SALIENCE = load_salience()


# =========================================================
# RAW ACCESS LAYER (NO ABSTRACTION, NO QUERY ENGINE)
# =========================================================

def raw_salience():
    return SALIENCE


# NOTE:
# Plugins may diverge semantically and structurally.
# Only visual CSS classes are considered shared constraints.


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
# PLUGIN CORE
# =========================================================

def run_plugin(name, fn, soup, url, salience):
    print(f"🔌 plugin: {name} → {url}")
    try:
        fn(soup, url, salience)
    except Exception as e:
        print(f"⚠️ plugin failed [{name}]: {e}")


# =========================================================
# PLUGINS (RAW SALIENCE CONSUMERS ONLY)
# =========================================================

# ---------------------------------------------------------
# RELATED CONTENT (direct graph interpretation)
# ---------------------------------------------------------

def plugin_related_content(soup, url, salience):
    for old in soup.select("section.related-paths"):
        old.decompose()

    pages = salience.get("pages", {})
    if not isinstance(pages, dict):
        return {}

    node = pages.get(url, {})
    concepts = node.get("concepts", [])

    if not concepts:
        return

    scores = {}

    for concept in concepts:
        word = concept.get("word") if isinstance(concept, dict) else concept
        if not word:
            continue

        for other_url, other_node in pages.items():
            if other_url == url:
                continue

            other_concepts = other_node.get("concepts", [])

            for oc in other_concepts:
                oword = oc.get("word") if isinstance(oc, dict) else oc
                if oword == word:
                    scores[other_url] = scores.get(other_url, 0) + 1

    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:5]
    related = [u for u, _ in ranked]

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


# ---------------------------------------------------------
# TRACKING (NON-SEMANTIC)
# ---------------------------------------------------------

def plugin_tracking(soup, url, salience):
    if soup.find("script", {"src": TRACKER_PATH}):
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True

    if soup.body:
        soup.body.append(script)
    else:
        soup.append(script)


# ---------------------------------------------------------
# HOMEPAGE INTELLIGENCE (RAW SALIENCE SCAN)
# ---------------------------------------------------------

def plugin_homepage_intelligence(soup, url, salience):
    for old in soup.select("section.homepage-intelligence"):
        old.decompose()

    pages = salience.get("pages", {})
    if not isinstance(pages, dict):
        return {}

    scored = []

    for u, node in pages.items():
        if u == url:
            continue

        weight = 0.0
        for c in node.get("concepts", []):
            if isinstance(c, dict):
                weight += float(c.get("weight", 1.0))
            else:
                weight += 1.0

        scored.append((u, weight))

    scored.sort(key=lambda x: (-x[1], x[0]))
    top = [u for u, _ in scored[:3]]

    if not top:
        return

    root = soup.new_tag("section")
    root["class"] = "homepage-intelligence"

    h = soup.new_tag("h2")
    h.string = "Homepage intelligence"
    root.append(h)

    cloud = soup.new_tag("div")
    cloud["class"] = "chip-cloud"

    for node_url in top:
        a = soup.new_tag("a", href=node_url.replace("https://unboundhealing.org", ""))
        a["class"] = "chip"
        a.string = fallback_title(node_url)
        cloud.append(a)

    root.append(cloud)

    if soup.body:
        soup.body.append(root)
    else:
        soup.append(root)


# =========================================================
# PLUGIN REGISTRY (INTERNAL ONLY)
# =========================================================

PLUGIN_ORDER = [
    "related_content",
    "tracking",
    "homepage_intelligence",
]

PLUGIN_REGISTRY = {
    "related_content": plugin_related_content,
    "tracking": plugin_tracking,
    "homepage_intelligence": plugin_homepage_intelligence,
}

ACTIVE_PLUGINS = PLUGIN_ORDER


# =========================================================
# PIPELINE
# =========================================================

def enhance_page(soup, url):
    for name in ACTIVE_PLUGINS:
        fn = PLUGIN_REGISTRY.get(name)
        if fn:
            run_plugin(name, fn, soup, url, raw_salience())

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

    print("✅ Semantic-salience consumer layer complete (fully collapsed, direct interpretation model)")


if __name__ == "__main__":
    main()
