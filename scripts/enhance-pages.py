import json
import os
import re
from bs4 import BeautifulSoup

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")
PAGE_TITLES_FILE = os.path.join(ROOT, "page-titles.json")

TRACKER_PATH = "/assets/js/semantic-tracker.js"


# =========================================================
# DATA LOADING
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
    files = []

    for root, _, fns in os.walk(ROOT):

        if "/assets/" in root.replace("\\", "/"):
            continue

        for f in fns:
            if f.endswith(".html"):
                files.append(os.path.join(root, f))

    return files


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
# CONTEXT LAYER (STRICT SINGLE SOURCE OF TRUTH)
# =========================================================

def build_context(url):
    node = salience.get(url, {})

    related = [
        item["url"]
        for item in node.get("related", [])
        if item.get("url") != url
    ][:5]

    return {
        "url": url,
        "title": lookup_title(url),
        "related": related,

        # DEBUG ONLY (safe to remove later)
        "raw": node,
    }


# =========================================================
# PLUGIN SYSTEM
# =========================================================

def run_plugin(name, fn, soup, context):
    try:
        fn(soup, context)
    except Exception as e:
        print(f"⚠️ Plugin failed [{name}] -> {e}")


# =========================================================
# PLUGINS (CONTEXT ONLY — NO GLOBAL DATA ACCESS)
# =========================================================

def plugin_related_content(soup, context):

    # idempotent cleanup
    for old in soup.select("section.related-paths"):
        old.decompose()

    related = context.get("related", [])

    if not related:
        return

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
            href=r.replace("https://unboundhealing.org", "")
        )
        a["class"] = "related-chip"
        a.string = lookup_title(r)
        cloud.append(a)

    block.append(cloud)

    footer = soup.find("footer")

    if footer:
        footer.insert_before(block)
    elif soup.body:
        soup.body.append(block)


def plugin_tracking(soup, context):

    if soup.find("script", {"src": TRACKER_PATH}):
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True

    if soup.body:
        soup.body.append(script)
    else:
        soup.append(script)


def plugin_future_magic(soup, context):
    # reserved semantic expansion hook
    pass


# =========================================================
# REGISTRY (DATA-DRIVEN EXECUTION LAYER)
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
# ENGINE CORE (CONTEXT-LOCKED EXECUTION)
# =========================================================

def enhance_page(soup, url):

    context = build_context(url)

    for name in ACTIVE_PLUGINS:
        plugin = PLUGIN_REGISTRY.get(name)

        if not plugin:
            print(f"⚠️ Unknown plugin: {name}")
            continue

        run_plugin(name, plugin, soup, context)

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
