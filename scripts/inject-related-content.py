#!/usr/bin/env python3

import json
import os
from bs4 import BeautifulSoup

# =========================================================
# ROOT
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")
PAGE_TITLES_FILE = os.path.join(ROOT, "page-titles.json")

DOMAIN = "https://unboundhealing.org/"


# =========================================================
# LOAD SINGLE TRUTH LAYER (HARD REQUIREMENT)
# =========================================================

with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
    semantic = json.load(f)

PAGE_GRAPH = semantic["page_graph"]


# =========================================================
# LOAD PAGE TITLES
# =========================================================

if os.path.exists(PAGE_TITLES_FILE):
    with open(PAGE_TITLES_FILE, "r", encoding="utf-8") as f:
        page_titles = json.load(f)
else:
    page_titles = {}


# =========================================================
# CANONICAL URL SYSTEM (SINGLE SOURCE OF TRUTH)
# =========================================================

def canonicalize(url: str) -> str:
    url = url.strip()

    if not url.startswith("http"):
        url = f"{DOMAIN}{url}"

    url = url.replace("index.html", "").replace(".html", "")

    # normalize trailing slash
    url = url.rstrip("/") + "/"

    return url


# =========================================================
# FILE DISCOVERY
# =========================================================

def find_html_files():
    html_files = []

    for root, _, files in os.walk(ROOT):

        if "/assets/" in root.replace("\\", "/"):
            continue

        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))

    return html_files


# =========================================================
# FILE → URL (MATCHES GRAPH EXACTLY VIA CANONICALIZE)
# =========================================================

def get_url_from_file(file_path):
    rel = file_path.replace(ROOT, "")
    rel = rel.replace("\\", "/")

    rel = rel.replace("index.html", "").replace(".html", "")

    if rel.startswith("/"):
        rel = rel[1:]

    return canonicalize(rel)


# =========================================================
# TITLE RESOLUTION
# =========================================================

def lookup_title(url):
    url = canonicalize(url)

    path = url.replace(DOMAIN, "").strip("/")
    key = "/" if not path else f"/{path}/"

    if key in page_titles:
        return page_titles[key]

    slug = path.split("/")[-1] if path else ""
    return slug.replace("-", " ").title() if slug else "Home"


# =========================================================
# TRUTH LAYER ACCESS
# =========================================================

def get_related(url, limit=3):
    url = canonicalize(url)

    node = PAGE_GRAPH.get(url)

    if not node:
        return []

    related = node.get("related", [])

    cleaned = []
    seen = set()

    for r in related:
        if not r:
            continue

        r = canonicalize(r)

        if r in seen:
            continue

        seen.add(r)
        cleaned.append(r)

        if len(cleaned) >= limit:
            break

    return cleaned


# =========================================================
# INJECTION ENGINE
# =========================================================

def inject_related_content(file_path):

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # remove old injections (idempotent)
        for old in soup.select("section.related-paths"):
            old.decompose()

        url = get_url_from_file(file_path)
        related_urls = get_related(url)

        if not related_urls:
            return

        block = soup.new_tag("section")
        block["class"] = "related-paths"

        heading = soup.new_tag("h3")
        heading.string = "Further paths to ponder…"
        block.append(heading)

        cloud = soup.new_tag("div")
        cloud["class"] = "related-cloud"

        for r in related_urls:

            a = soup.new_tag("a")

            # IMPORTANT: make links relative, but stable
            href = r.replace(DOMAIN, "").rstrip("/")
            if not href.startswith("/"):
                href = "/" + href

            a["href"] = href
            a["class"] = "related-chip"
            a.string = lookup_title(r)

            cloud.append(a)

        block.append(cloud)

        footer = soup.find("footer")

        if footer:
            footer.insert_before(block)
        elif soup.body:
            soup.body.append(block)
        else:
            soup.append(block)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

        print(f"🔗 Injected related paths into {file_path}")

    except Exception as e:
        print(f"⚠️ Skipped {file_path}: {e}")


# =========================================================
# ENTRYPOINT
# =========================================================

def main():
    html_files = find_html_files()

    for file_path in html_files:
        inject_related_content(file_path)

    print("✅ Related-content injection complete (canonicalized graph v5.0)")


if __name__ == "__main__":
    main()
