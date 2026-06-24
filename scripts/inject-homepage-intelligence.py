#!/usr/bin/env python3

import os
import json
from bs4 import BeautifulSoup

# =========================================================
# ROOT + FILES
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTELLIGENCE_FILE = os.path.join(ROOT, "homepage-intelligence.json")


# =========================================================
# LOAD DERIVED INTELLIGENCE (CONSUMER MODEL ONLY)
# =========================================================

def load_intelligence():
    """
    Consumer-only projection of semantic-salience.
    Never reinterprets meaning.
    """
    if not os.path.exists(INTELLIGENCE_FILE):
        return {}

    try:
        with open(INTELLIGENCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    return data.get("homepage_intelligence", {})


intel = load_intelligence()


# =========================================================
# SAFE HELPERS
# =========================================================

def safe_list(x):
    return x if isinstance(x, list) else []


def limit_3(items):
    return items[:3]


def ensure_body(soup):
    if soup.body:
        return soup.body

    body = soup.new_tag("body")
    soup.append(body)
    return body


def normalize_url(url):
    if not url:
        return "#"
    return url.replace("https://unboundhealing.org", "")


def chip(soup, text, href):
    a = soup.new_tag("a", href=href)
    a["class"] = "chip"
    a.string = text
    return a


# =========================================================
# BLOCK REMOVAL (PREVENT DUPLICATION)
# =========================================================

def remove_existing(soup):
    for sel in [
        ".arising-observations",
        ".essential-inspirations",
        ".related-paths",
        ".homepage-intelligence"
    ]:
        for el in soup.select(sel):
            el.decompose()


# =========================================================
# BUILD SECTIONS (STRICT 3 ITEM RULE)
# =========================================================

def build_arising_observations(soup):
    hubs = limit_3(safe_list(intel.get("top_hubs", [])))
    if not hubs:
        return

    body = ensure_body(soup)

    section = soup.new_tag("section")
    section["class"] = "arising-observations"

    h2 = soup.new_tag("h2")
    h2.string = "Arising observations"
    section.append(h2)

    cloud = soup.new_tag("div")
    cloud["class"] = "chip-cloud"

    for item in hubs:
        node = item.get("node", "")
        href = normalize_url(node)
        label = node.split("/")[-1] if node else "observation"
        cloud.append(chip(soup, label, href))

    section.append(cloud)
    body.append(section)


def build_essential_inspirations(soup):
    concepts = limit_3(safe_list(intel.get("top_concepts", [])))
    if not concepts:
        return

    body = ensure_body(soup)

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

        cloud.append(chip(
            soup,
            concept,
            f"/concept/{concept}/"
        ))

    section.append(cloud)
    body.append(section)


def build_further_paths(soup, url):
    related = limit_3(safe_list(intel.get("top_hubs", [])))
    if not related:
        return

    body = ensure_body(soup)

    section = soup.new_tag("section")
    section["class"] = "related-paths"

    h3 = soup.new_tag("h3")
    h3.string = "Further paths to follow"
    section.append(h3)

    cloud = soup.new_tag("div")
    cloud["class"] = "related-cloud"

    for item in related:
        node = item.get("node", "") if isinstance(item, dict) else str(item)

        href = normalize_url(node)
        label = node.split("/")[-1] if node else "path"

        cloud.append(chip(soup, label, href))

    section.append(cloud)
    body.append(section)


# =========================================================
# PAGE TYPE DETECTION
# =========================================================

def is_homepage(url):
    return url.rstrip("/") == "https://unboundhealing.org"


# =========================================================
# INJECT CORE
# =========================================================

def inject(file_path, url):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    remove_existing(soup)

    # HOME ONLY BLOCKS
    if is_homepage(url):
        build_arising_observations(soup)
        build_essential_inspirations(soup)

    # ALL PAGES BLOCK
    build_further_paths(soup, url)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


# =========================================================
# FILE DISCOVERY
# =========================================================

def find_html_files():
    files = []

    for root, _, fs in os.walk(ROOT):
        norm = root.replace("\\", "/")

        if "/assets/" in norm:
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
            print(f"✨ Injected homepage intelligence → {url}")
        except Exception as e:
            print(f"⚠️ Failed {f}: {e}")

    print("✅ Homepage intelligence injection complete (consumer-only layer)")


if __name__ == "__main__":
    main()
