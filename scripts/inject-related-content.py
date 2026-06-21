import json
import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

PAGE_TITLES_FILE = os.path.join(ROOT, "page-titles.json")
SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")

# -----------------------------
# Load salience (ONLY SOURCE OF TRUTH)
# -----------------------------
with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
    salience = json.load(f)

# -----------------------------
# Load page titles
# -----------------------------
if os.path.exists(PAGE_TITLES_FILE):
    with open(PAGE_TITLES_FILE, "r", encoding="utf-8") as f:
        page_titles = json.load(f)
else:
    page_titles = {}

# -----------------------------
# Build reverse index: URL → salience group
# -----------------------------
url_to_group = {}
group_to_pages = {}

for group_key, group_data in salience.items():
    pages = group_data.get("pages", [])

    group_to_pages[group_key] = pages

    for p in pages:
        url_to_group[p["url"]] = group_key

# -----------------------------
# Helpers
# -----------------------------
def find_html_files():
    html_files = []
    for root, _, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))
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
    path = (
        url.replace("https://unboundhealing.org", "")
        .rstrip("/")
    )

    key = "/" if path == "" else f"{path}/"

    title = page_titles.get(key)
    if title:
        return title

    slug = key.strip("/").split("/")[-1]
    return slug.replace("-", " ").title()


# -----------------------------
# Injection
# -----------------------------
HTML_FILES = find_html_files()

for file in HTML_FILES:

    try:
        with open(file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # Remove previous injections
        for old in soup.select("section.related-paths"):
            old.decompose()

        url = get_url_from_file(file)

        if url not in url_to_group:
            continue

        group = url_to_group[url]
        pages = group_to_pages.get(group, [])

        # remove current page + limit
        related = [
            p["url"]
            for p in pages
            if p["url"] != url
        ][:5]

        if not related:
            continue

        # Create section
        block = soup.new_tag("section")
        block["class"] = "related-paths"

        heading = soup.new_tag("h3")
        heading.string = "Further paths to ponder…"
        block.append(heading)

        cloud = soup.new_tag("div")
        cloud["class"] = "related-cloud"

        for r in related:
            a = soup.new_tag("a", href=r.replace("https://unboundhealing.org", ""))
            a["class"] = "related-chip"
            a.string = lookup_title(r)
            cloud.append(a)

        block.append(cloud)

        # Insert
        footer = soup.find("footer")

        if footer:
            footer.insert_before(block)
        elif soup.body:
            soup.body.append(block)

        with open(file, "w", encoding="utf-8") as f:
            f.write(str(soup))

        print(f"🔗 Injected related paths into {file}")

    except Exception as e:
        print(f"⚠️ Skipped {file}: {e}")

print("✅ Phase 3 injection complete")
