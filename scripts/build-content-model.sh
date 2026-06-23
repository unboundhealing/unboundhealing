#!/bin/bash
set -e

echo "🧠 Building content model (v4.2 JSON-safe pipeline)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-model.json"

# ==========================================================
# PYTHON-DRIVEN MODEL GENERATION (NO SHELL JSON)
# ==========================================================

python3 << 'EOF'
import json
import os
from bs4 import BeautifulSoup

print("🧪 CONTENT MODEL DIAGNOSTICS")

pages = []

for root, _, files in os.walk("."):
    for file in files:
        if not file.endswith(".html"):
            continue

        path = os.path.join(root, file)

        try:
            with open(path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")

            url = path \
                .replace("./", "") \
                .replace("index.html", "") \
                .replace(".html", "")

            url = "https://unboundhealing.org/" + url

            title = soup.title.get_text(strip=True) if soup.title else ""
            desc_tag = soup.find("meta", attrs={"name": "description"})
            desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""

            body = soup.get_text(" ", strip=True)[:300]

            # SAFE TAG EXTRACTION
            tags = []

            for h in soup.find_all(["h1", "h2"]):
                t = h.get_text(strip=True).lower()
                if t:
                    tags.append(t.replace(" ", "-"))

            # dedupe
            tags = list(dict.fromkeys(tags))

            pages.append({
                "url": url,
                "file": path,
                "title": title,
                "description": desc,
                "body_sample": body,
                "tags": tags
            })

        except Exception as e:
            print(f"⚠️ skipped {path}: {e}")

# ==========================================================
# WRITE SAFE JSON (NO MANUAL ESCAPING)
# ==========================================================

with open("content-model.json", "w", encoding="utf-8") as f:
    json.dump({"pages": pages}, f, indent=2, ensure_ascii=False)

# ==========================================================
# DIAGNOSTICS
# ==========================================================

print("\n🧪 MODEL SUMMARY")
print("pages:", len(pages))

tag_count = sum(len(p.get("tags", [])) for p in pages)
print("total tagged entries:", tag_count)

print("\nSAMPLE PAGE")
if pages:
    print(json.dumps(pages[0], indent=2)[:1500])

print("\n✅ content model built (v4.2 JSON-safe)")
EOF

echo "✅ Content model built"
