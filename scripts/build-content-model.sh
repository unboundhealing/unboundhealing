#!/usr/bin/env bash
set -euo pipefail

echo "🧠 Building content model (v4.3 hardened JSON-safe pipeline)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-model.json"

python3 - <<'PY'
import os
import json
import re
from bs4 import BeautifulSoup

root = os.getcwd()

pages = []

def safe_text(x):
    if not x:
        return ""
    return str(x).strip()

def extract_tags_from_body(text):
    # stable semantic fallback (prevents explosion)
    if not text:
        return []
    words = re.findall(r"[a-zA-Z0-9\-]{4,}", text.lower())
    # deterministic, capped
    return sorted(set(words))[:25]

print("🧠 Scanning HTML files...")

for dirpath, _, filenames in os.walk(root):
    for f in filenames:
        if not f.endswith(".html"):
            continue

        path = os.path.join(dirpath, f)

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                soup = BeautifulSoup(file.read(), "html.parser")

            title = safe_text(soup.title.string if soup.title else "")

            meta = soup.find("meta", attrs={"name": "description"})
            description = safe_text(meta.get("content") if meta else "")

            body_text = safe_text(soup.get_text(" ", strip=True))
            body_sample = body_text[:300]

            # URL normalization
            url = path.replace(root, "").replace("./", "/")
            url = re.sub(r"index\.html$", "", url)
            url = re.sub(r"\.html$", "", url)
            url = "https://unboundhealing.org" + url

            tags = extract_tags_from_body(body_text)

            pages.append({
                "url": url,
                "file": path,
                "title": title,
                "description": description,
                "body_sample": body_sample,
                "tags": tags
            })

        except Exception as e:
            print(f"⚠️ Skipping {path}: {e}")

model = {
    "pages": pages
}

with open("content-model.json", "w", encoding="utf-8") as f:
    json.dump(model, f, ensure_ascii=False, indent=2)

print("")
print("🧪 CONTENT MODEL DIAGNOSTICS")
print(f"📦 pages processed: {len(pages)}")
print(f"📁 output: content-model.json")

# quick sample safety check
if pages:
    print("")
    print("🧪 SAMPLE PAGE")
    print(json.dumps(pages[0], indent=2)[:1200])

print("")
print("✅ content model built (v4.3 hardened JSON-safe pipeline)")
PY

echo "🔗 Content model build complete"
