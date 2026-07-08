#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd())).resolve()

TRACKER_PATH = os.environ.get(
    "SEMANTIC_TRACKER_PATH",
    "/assets/js/semantic-tracker.js"
)

SCRIPT = (
    f'<!-- semantic-tracker -->\n'
    f'<script defer src="{TRACKER_PATH}" '
    f'data-salience-tracking="true"></script>'
)


def find_html_files():

    files = []

    for path in ROOT.rglob("*.html"):

        if "/assets/" in str(path).replace("\\", "/"):
            continue

        files.append(path)

    return files


def inject_tracking(path: Path):

    original = path.read_text(encoding="utf-8")

    if TRACKER_PATH in original:
        print(f"📡 already present → {path}")
        return

    updated = original.replace(
        "</body>",
        f"{SCRIPT}\n</body>"
    )

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print(f"⚠️  Tracker missing → {path}")
        print(f"✅  Automatically repaired")

def main():

    html_files = find_html_files()

    print(f"🔎 tracking scan → {len(html_files)} files")

    for path in html_files:
        try:
            inject_tracking(path)

        except Exception as e:
            print(f"⚠️ skipped {path}: {e}")

    print("✅ Tracking injection complete (v5 fully standalone consumer)")


if __name__ == "__main__":
    main()
