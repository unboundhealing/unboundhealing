#!/usr/bin/env python3

import os
import json
from bs4 import BeautifulSoup

# =========================================================
# ROOT
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTELLIGENCE_FILE = os.path.join(ROOT, "homepage-intelligence.json")

# =========================================================
# LOAD CONSUMER MODEL ONLY
# =========================================================

def load_intelligence():
    if not os.path.exists(INTELLIGENCE_FILE):
        raise FileNotFoundError("❌ homepage-intelligence.json missing")

    with open(INTELLIGENCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("homepage_intelligence", {})


intel = load_intelligence()


# =========================================================
# SAFE HELPERS
# =========================================================

def safe_list(items):
    if not isinstance(items, list):
        return []
    return items


def chunk_3(items):
    return items[:3]


def make_chip(soup, text, href):
    a = soup.new_tag("a", href=href)
    a["class"] = "chip"
    a.string = text
    return a


# =========================================================
# URL HELPERS
# =========================================================

def normalize_url(url):
    if not url:
        return "#"
    return url.replace("https://unboundhealing.org", "")


# =========================================================
# BUILD BLOCKS
# =========================================================

def build_arising_observations(soup):
    hubs = safe_list(intel.get("top_hubs", []))[:3]

    if not hubs:
        return

    section = soup.new_tag("section")
    section["class"] = "arising-observations"

    h2 = soup.new_tag("h2")
    h2.string = "Arising observations"
    section.append(h2)

    cloud = soup.new_tag("div")
    cloud["class"] = "chip-cloud"

    for item in hubs:
        node = item.get("node")
        href = normalize_url(node)
        cloud.append(make_chip(soup, node.split("/")[-1], href))

    section.append(cloud)
    soup.body.append(section)


def build_essential_inspirations(soup):
    concepts = safe_list(intel.get("top_concepts", []))[:3]

    if not concepts:
        return

    section = soup.new_tag("section")
    section["class"] = "essential-inspirations"

    h2 = soup.new_tag("h2")
    h2.string = "Essential inspirations"
    section.append(h2)

    cloud = soup.new_tag("div")
    cloud["class"] = "chip-cloud"

    for c in concepts:
        concept = c.get("concept", "")
        if not concept:
            continue

        cloud.append(make_chip(soup, concept, f"/concept/{concept}/"))

    section.append(cloud)
    soup.body.append(section)


def build_further_paths(soup, url):
    related = []  # intentionally left minimal (hook point for future salience query layer)

    # fallback: reuse hubs if no related passed in
    if not related:
        related = safe_list(intel.get("top_hubs", []))[:3]

    if not related:
        return

    section = soup.new_tag("section")
    section["class"] = "related-paths"

    h3 = soup.new_tag("h3")
    h3.string = "Further paths to follow"
    section.append(h3)

    cloud = soup.new_tag("div")
    cloud["class"] = "related-cloud"

    for item in related:
        if isinstance(item, dict):
            node = item.get("node", "")
        else:
            node = str(item)

        href = normalize_url(node)
        label = node.split("/")[-1] if node else "path"

        cloud.append(make_chip(soup, label, href))

    section.append(cloud)
    soup.body.append(section)


# =========================================================
# CLEAN EXISTING BLOCKS (PREVENT DUPLICATION)
# =========================================================

def remove_existing_blocks(soup):
    for sel in [
        ".arising-observations",
        ".essential-inspirations",
        ".related-paths"
    ]:
        for el in soup.select(sel):
            el.decompose()


# =========================================================
# PAGE TYPE DETECTION
# =========================================================

def is_homepage(url):
    return url.rstrip("/") == "https://unboundhealing.org"


# =========================================================
# INJECTION CORE
# =========================================================

def inject(file_path, url):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    remove_existing_blocks(soup)

    # ALWAYS safe re-inject
    if is_homepage(url):
        build_arising_observations(soup)
        build_essential_inspirations(soup)

    # ALL pages
    build_further_paths(soup, url)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


# =========================================================
# FILE DISCOVERY
# =========================================================

def find_html_files():
    files = []

    for root, _, fs in os.walk(ROOT):
        if "/assets/" in root.replace("\\", "/"):
            continue

        for f in fs:
            if f.endswith(".html"):
                files.append(os.path.join(root, f))

    return files


# =========================================================
# URL MAP
# =========================================================

def file_to_url(path):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    rel = rel.replace("index.html", "").replace(".html", "").strip("/")
    return f"https://unboundhealing.org/{rel}" if rel else "https://unboundhealing.org/"


# =========================================================
# MAIN
# =========================================================

def main():
    files = find_html_files()

    for f in files:
        try:
            url = file_to_url(f)
            inject(f, url)
            print(f"✨ Injected intelligence → {url}")
        except Exception as e:
            print(f"⚠️ Failed {f}: {e}")

    print("✅ Homepage intelligence injection complete (consumer-only layer)")


if __name__ == "__main__":
    main()
