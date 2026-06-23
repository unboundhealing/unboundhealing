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

# HARD TRUTH CONTRACT:
# If page_graph is missing, this consumer MUST fail loudly.
PAGE_GRAPH = semantic["page_graph"]


# =========================================================
# LOAD PAGE TITLES (OPTIONAL CONSUMER ENRICHMENT)
# =========================================================

if os.path.exists(PAGE_TITLES_FILE):
    with open(PAGE_TITLES_FILE, "r", encoding="utf-8") as f:
        page_titles = json.load(f)
else:
    page_titles = {}


# =========================================================
# FILE DISCOVERY
# =========================================================

def find_html_files():
    """
    Structural scan only.
    No semantic interpretation.
    """
    html_files = []

    for root, _, files in os.walk(ROOT):

        # skip assets (non-content layer)
        if "/assets/" in root.replace("\\", "/"):
            continue

        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))

    return html_files


# =========================================================
# URL RESOLUTION (STRUCTURAL ONLY)
# =========================================================

def get_url_from_file(file_path):
    """
    NOTE:
    This is a structural mapping only.
    Canonical identity is defined by semantic-salience graph keys.
    """

    rel = file_path.replace(ROOT, "")

    # normalize filesystem artifact only
    rel = rel.replace("\\", "/")

    # strip HTML artifacts
    rel = rel.replace("index.html", "").replace(".html", "")

    if rel.startswith("/"):
        rel = rel[1:]

    return f"{DOMAIN}{rel}"


# =========================================================
# TITLE RESOLUTION (PURE UI LAYER)
# =========================================================

def lookup_title(url):
    path = url.replace(DOMAIN, "").rstrip("/")
    key = "/" if path == "" else f"/{path}/"

    if key in page_titles:
        return page_titles[key]

    slug = key.strip("/").split("/")[-1]
    return slug.replace("-", " ").title() if slug else "Home"


# =========================================================
# TRUTH LAYER ACCESS (ONLY RELATION SOURCE)
# =========================================================

def get_related(url, limit=3):
    """
    SINGLE SOURCE OF TRUTH:

    page_graph is the only valid relationship system.

    This consumer:
    - does NOT compute relationships
    - does NOT infer similarity
    - does NOT rank semantics
    """

    node = PAGE_GRAPH.get(url)

    if not node:
        return []

    # graph-derived neighbors (already ordered upstream)
    related = node.get("related", [])

    cleaned = []
    seen = set()

    for r in related:
        if not r or r in seen:
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

        # -------------------------------------------------
        # REMOVE PREVIOUS INJECTIONS (IDEMPOTENT BEHAVIOR)
        # -------------------------------------------------
        for old in soup.select("section.related-paths"):
            old.decompose()

        url = get_url_from_file(file_path)

        related_urls = get_related(url)

        if not related_urls:
            return

        # -------------------------------------------------
        # BUILD UI BLOCK (PURE PRESENTATION LAYER)
        # -------------------------------------------------

        block = soup.new_tag("section")
        block["class"] = "related-paths"

        heading = soup.new_tag("h3")
        heading.string = "Further paths to ponder…"
        block.append(heading)

        cloud = soup.new_tag("div")
        cloud["class"] = "related-cloud"

        for r in related_urls:

            a = soup.new_tag(
                "a",
                href=r.replace(DOMAIN, "")
            )

            a["class"] = "related-chip"
            a.string = lookup_title(r)

            cloud.append(a)

        block.append(cloud)

        # -------------------------------------------------
        # INSERT STRATEGY (DOM SAFE)
        # -------------------------------------------------

        footer = soup.find("footer")

        if footer:
            footer.insert_before(block)
        elif soup.body:
            soup.body.append(block)
        else:
            # hard fallback: append to document root
            soup.append(block)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

        print(f"🔗 Injected related paths into {file_path}")

    except Exception as e:
        # fail-soft for CI stability, but log clearly
        print(f"⚠️ Skipped {file_path}: {e}")


# =========================================================
# ENTRYPOINT
# =========================================================

def main():
    html_files = find_html_files()

    for file_path in html_files:
        inject_related_content(file_path)

    print("✅ Related-content injection complete (page_graph single-truth consumer v4.1)")


if __name__ == "__main__":
    main()
