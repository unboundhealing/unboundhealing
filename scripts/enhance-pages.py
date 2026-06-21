import json
import os
import re
from bs4 import BeautifulSoup

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")
PAGE_TITLES_FILE = os.path.join(ROOT, "page-titles.json")

TRACKER_PATH = "/assets/js/semantic-tracker.js"


# -----------------------------
# Load data
# -----------------------------
with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
    salience = json.load(f)

if os.path.exists(PAGE_TITLES_FILE):
    with open(PAGE_TITLES_FILE, "r", encoding="utf-8") as f:
        page_titles = json.load(f)
else:
    page_titles = {}


# -----------------------------
# Helpers
# -----------------------------
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


# -----------------------------
# Injection: Related Content
# -----------------------------
def inject_related_content(soup, url):

    for old in soup.select("section.related-paths"):
        old.decompose()

    if url not in salience:
        return

    related_items = salience[url].get("related", [])

    related = [
        r["url"]
        for r in related_items
        if r["url"] != url
    ][:5]

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


# -----------------------------
# Injection: Tracking
# -----------------------------
def inject_tracking(soup):

    if soup.find("script", {"src": TRACKER_PATH}):
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True

    if soup.body:
        soup.body.append(script)
    else:
        soup.append(script)


# -----------------------------
# Future Hook (OG / schema / etc.)
# -----------------------------
def inject_future_magic(soup, url):
    pass


# -----------------------------
# SINGLE PASS PIPELINE
# -----------------------------
def enhance_page(soup, url):

    inject_related_content(soup, url)
    inject_tracking(soup)
    inject_future_magic(soup, url)

    return soup


# -----------------------------
# Main loop (single pass)
# -----------------------------
HTML_FILES = find_html_files()

for file in HTML_FILES:

    try:
        with open(file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        url = get_url_from_file(file)

        soup = enhance_page(soup, url)

        with open(file, "w", encoding="utf-8") as f:
            f.write(str(soup))

        print(f"✨ Enhanced {file}")

    except Exception as e:
        print(f"⚠️ Skipped {file}: {e}")

print("✅ Single-pass enhancement complete")
