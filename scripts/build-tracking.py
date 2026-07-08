#!/usr/bin/env python3

import os
from pathlib import Path
from bs4 import BeautifulSoup

# =========================================================
# ROOT
# =========================================================

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd())).resolve()

# =========================================================
# TRACKER CONFIG (SIDE-EFFECT ONLY)
# =========================================================

TRACKER_PATH = os.environ.get(
    "SEMANTIC_TRACKER_PATH",
    "/assets/js/semantic-tracker.js"
)

PLACEHOLDER = "<!-- semantic-tracker -->"

# =========================================================
# FILE DISCOVERY (PURE STRUCTURAL SCAN)
# =========================================================

def find_html_files():
    """
    Finds all HTML files except asset pipeline.
    """

    files = []

    for path in ROOT.rglob("*.html"):

        if "/assets/" in str(path).replace("\\", "/"):
            continue

        files.append(path)

    return files

# =========================================================
# TRACKER INJECTION (IDEMPOTENT SIDE EFFECT)
# =========================================================

def inject_tracking_script(soup):
    """
    Pure deterministic DOM injection.

    No dependencies on:
    - semantic-salience
    - homepage-intelligence
    - related-content
    """

    # ---------------------------------------------
    # IDEMPOTENCY CHECK
    # ---------------------------------------------

    if soup.find("script", {"src": TRACKER_PATH}):
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True
    script["data-salience-tracking"] = "true"

    # ---------------------------------------------
    # INSERTION STRATEGY (SAFE ORDERED FALLBACK)
    # ---------------------------------------------

    if soup.body:
        soup.body.append(script)
    elif soup.head:
        soup.head.append(script)
    else:
        soup.append(script)

# =========================================================
# FILE PROCESSOR
# =========================================================

def process_file(path: Path):

    try:

        original = path.read_text(encoding="utf-8")

        soup = BeautifulSoup(original, "html.parser")

        # If tracker already exists, leave the file completely untouched.
        if soup.find("script", {"src": TRACKER_PATH}):
            print(f"📡 already present → {path}")
            return

        inject_tracking_script(soup)

        updated = str(soup)

        if updated != original:
            path.write_text(updated, encoding="utf-8")
            print(f"📡 CHANGED → {path}")
        else:
            print(f"📡 unchanged → {path}")

    except Exception as e:
        print(f"⚠️ skipped {path}: {e}")

# =========================================================
# MAIN
# =========================================================

def main():

    html_files = find_html_files()

    print(f"🔎 tracking scan → {len(html_files)} files")

    for path in html_files:
        process_file(path)

    print("✅ Tracking injection complete (v5 fully standalone consumer)")


if __name__ == "__main__":
    main()
