#!/bin/bash
set -e

echo "🧠 Building content model (v4.0 content-derived concepts)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-model.json"
TMP_OUTPUT="${OUTPUT}.tmp"

rm -f "$TMP_OUTPUT"

python3 << 'EOF'
import json
import os
import re
from collections import Counter
from bs4 import BeautifulSoup

OUTPUT = "content-model.json"

# ==========================================================
# CONFIG
# ==========================================================

STOPWORDS = {
    "the","and","for","are","with","that","this","from","into",
    "your","their","there","about","would","could","should",
    "have","been","being","were","they","them","then","than",
    "when","what","where","which","while","will","just",
    "through","within","without","because","also","very",
    "much","more","some","such","each","many","most",
    "into","onto","upon","over","under","between",
    "unbound","healing","ministries"
}

SKIP_PATHS = {
    "./assets/entry-template/index.html",
    "./assets/page-template/index.html",
    "./assets/updates-temp/index.html"
}

SKIP_CONTAINS = [
    "/assets/images/",
    "/assets/_html/"
]

MAX_TAGS = 15

# ==========================================================
# HELPERS
# ==========================================================

def extract_text(soup):
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "header",
        "footer",
        "nav"
    ]):
        tag.decompose()

    return soup.get_text(" ", strip=True)

def normalize_word(word):
    word = word.lower().strip()

    word = re.sub(r"[^a-z\-]", "", word)

    if len(word) < 4:
        return None

    if word in STOPWORDS:
        return None

    if word.isdigit():
        return None

    return word

def build_tags(title, description, body):
    text = " ".join([
        title or "",
        description or "",
        body or ""
    ])

    words = re.findall(r"[A-Za-z\-]{4,}", text)

    cleaned = []

    for w in words:
        n = normalize_word(w)

        if n:
            cleaned.append(n)

    counts = Counter(cleaned)

    tags = [
        word
        for word, count
        in counts.most_common(MAX_TAGS)
    ]

    return tags

# ==========================================================
# DISCOVER HTML FILES
# ==========================================================

html_files = []

for root, dirs, files in os.walk("."):

    for file in files:

        if not file.endswith(".html"):
            continue

        path = os.path.join(root, file)

        if path in SKIP_PATHS:
            continue

        if any(x in path for x in SKIP_CONTAINS):
            continue

        html_files.append(path)

html_files = sorted(html_files)

# ==========================================================
# BUILD MODEL
# ==========================================================

pages = []

all_tags = []

print("\n🧪 CONTENT MODEL DIAGNOSTICS\n")

for idx, file in enumerate(html_files):

    with open(file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    url = (
        "https://unboundhealing.org/"
        + file.replace("./", "")
              .replace("index.html", "")
              .replace(".html", "")
    )

    title = ""

    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    description = ""

    meta = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    if meta and meta.get("content"):
        description = meta["content"].strip()

    body_text = extract_text(soup)

    tags = build_tags(
        title,
        description,
        body_text
    )

    all_tags.extend(tags)

    pages.append({
        "url": url,
        "file": file,
        "title": title,
        "description": description,
        "tags": tags
    })

    if idx < 10:
        print("=" * 70)
        print("URL:", url)
        print("TITLE:", title)
        print("DESCRIPTION:", description[:150])
        print("BODY SAMPLE:", body_text[:250])
        print("TAGS:", tags)
        print()

# ==========================================================
# GLOBAL DIAGNOSTICS
# ==========================================================

print("\n🧪 MODEL SUMMARY")
print("pages:", len(pages))

print("\nTOP 100 DISCOVERED TAGS")

for tag, count in Counter(all_tags).most_common(100):
    print(f"{tag}: {count}")

# ==========================================================
# SAVE
# ==========================================================

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(
        {
            "pages": pages
        },
        f,
        indent=2,
        ensure_ascii=False
    )

print("\n✅ Content model built (v4.0 content-derived concepts)")
print("📦 pages:", len(pages))
print("📦 unique tags:", len(set(all_tags)))
EOF

echo "✅ Content model built"
