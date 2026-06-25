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
# RAW ACCESS LAYER
# =========================================================

def raw_salience():
    return SALIENCE


# =========================================================
# CONTAINER RESOLUTION (NEW STANDARDIZED LAYER)
# =========================================================

def get_container(soup):
    return (
        soup.body.find("main")
        if soup.body and soup.body.find("main")
        else soup.body or soup
    )


def append_block(soup, block):
    container = get_container(soup)
    container.append(block)


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
# PLUGINS
# =========================================================

# ---------------------------------------------------------
# TRACKING
# ---------------------------------------------------------

def plugin_tracking(soup, url, salience):
    if soup.find("script", {"src": TRACKER_PATH}):
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True
    script["data-salience-debug"] = "true"

    append_block(soup, script)


# =========================================================
# REGISTRY
# =========================================================

PLUGIN_ORDER = [
    "tracking",
]

PLUGIN_REGISTRY = {
    "tracking": plugin_tracking,
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

    print("✅ Semantic-salience consumer layer complete (fully collapsed model)")


if __name__ == "__main__":
    main()
