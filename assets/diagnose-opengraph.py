#!/usr/bin/env python3

from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path.cwd()

EXCLUDED = [
    "assets/images/_html",
    "assets/page-template",
    "assets/entry-template",
    "assets/updates-temp",
]


def excluded(path: Path):
    p = path.as_posix()
    return any(x in p for x in EXCLUDED)


print("🧭 OpenGraph Diagnostics")
print("=" * 60)

pages = 0
warnings = 0
errors = 0

for html in sorted(ROOT.rglob("*.html")):

    rel = html.relative_to(ROOT)

    if excluded(rel):
        continue

    pages += 1

    soup = BeautifulSoup(
        html.read_text(encoding="utf-8", errors="ignore"),
        "html.parser"
    )

    title = soup.find("meta", property="og:title")
    description = soup.find("meta", property="og:description")
    image = soup.find("meta", property="og:image")
    url = soup.find("meta", property="og:url")

    page_messages = []

    if title is None:
        errors += 1
        page_messages.append("❌ missing og:title")

    if description is None:
        errors += 1
        page_messages.append("❌ missing og:description")

    if image is None:
        warnings += 1
        page_messages.append("⚠ missing og:image")

    if url is None:
        warnings += 1
        page_messages.append("⚠ missing og:url")

    if title and len(title.get("content", "")) > 60:
        warnings += 1
        page_messages.append("⚠ og:title > 60 chars")

    if description and len(description.get("content", "")) > 200:
        warnings += 1
        page_messages.append("⚠ og:description > 200 chars")

    if page_messages:
        print()
        print(rel)
        for msg in page_messages:
            print("   ", msg)

print()
print("=" * 60)
print(f"Pages scanned : {pages}")
print(f"Errors        : {errors}")
print(f"Warnings      : {warnings}")

if errors == 0:
    print("✅ Diagnostic complete")
else:
    print("⚠ Required OpenGraph fields are missing on one or more pages.")
