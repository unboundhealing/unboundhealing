#!/bin/bash
set -euo pipefail

echo "🧠 Building content model (v5 deterministic Python engine)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-model.json"
TMP_OUTPUT="content-model.tmp.json"

echo "🧠 Scanning HTML files..."

# -------------------------------------------------
# STABLE FILE DISCOVERY (NO mapfile, CI-safe)
# -------------------------------------------------
FILES=$(find . -type f -name "*.html" | sort)

COUNT=$(echo "$FILES" | sed '/^$/d' | wc -l | tr -d ' ')
echo "📦 pages discovered: $COUNT"

if [ "$COUNT" -eq 0 ]; then
  echo "❌ No HTML files found. Exiting."
  exit 1
fi

# -------------------------------------------------
# EXPORT FILE LIST TO PYTHON (deterministic boundary)
# -------------------------------------------------
export FILES

# -------------------------------------------------
# SINGLE PYTHON ENGINE (replaces entire fragile bash loop)
# -------------------------------------------------
python3 <<'PY' > "$TMP_OUTPUT"
import os
import json
import re
from bs4 import BeautifulSoup
from collections import Counter

files = [f for f in os.environ["FILES"].split("\n") if f.strip()]
files = sorted(files)

def safe_read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def extract_title(soup):
    try:
        return (soup.title.string or "").strip()
    except Exception:
        return ""

def extract_description(soup):
    try:
        m = soup.find("meta", attrs={"name": "description"})
        return m["content"].strip() if m and m.get("content") else ""
    except Exception:
        return ""

def extract_body(soup):
    try:
        text = soup.get_text(" ", strip=True)
        return text[:200]
    except Exception:
        return ""

def extract_tags(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())

    stop = {
        "the","and","for","with","that","this","from","you","are","was",
        "have","has","had","not","but","all","any","can","will","our"
    }

    filtered = [w for w in words if w not in stop]
    counts = Counter(filtered)
    return [w for w,_ in counts.most_common(20)]

pages = []

for file in files:
    html = safe_read(file)
    soup = BeautifulSoup(html, "html.parser")

    url = file.replace("./", "")
    url = re.sub(r"index\.html$", "", url)
    url = re.sub(r"\.html$", "", url)
    url = "https://unboundhealing.org/" + url.lstrip("/")

    text = soup.get_text(" ", strip=True)

    pages.append({
        "url": url,
        "file": file,
        "title": extract_title(soup),
        "description": extract_description(soup),
        "body_sample": extract_body(soup),
        "tags": extract_tags(text)
    })

json.dump({"pages": pages}, open(os.environ.get("OUTPUT_FILE","/dev/stdout"), "w"), indent=2)
PY

# -------------------------------------------------
# VALIDATE OUTPUT SAFELY
# -------------------------------------------------
echo "🧪 validating JSON..."

python3 <<PY
import json
with open("$TMP_OUTPUT","r") as f:
    json.load(f)
print("✅ JSON valid")
PY

# -------------------------------------------------
# ATOMIC WRITE
# -------------------------------------------------
mv "$TMP_OUTPUT" "$OUTPUT"

echo "✅ Content model built (v5 deterministic engine)"
echo "📁 output: $OUTPUT"
echo "📦 pages processed: $COUNT"
