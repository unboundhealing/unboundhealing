#!/bin/bash
set -euo pipefail

echo "🔎 Building search index (v5 unified python builder)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

SAL_FILE="semantic-salience.json"
OUTPUT="search-index.json"

if [ ! -f "$SAL_FILE" ]; then
  echo "❌ semantic-salience.json missing — HARD STOP"
  exit 1
fi

if [ ! -s "$SAL_FILE" ]; then
  echo "❌ semantic-salience.json is empty — HARD STOP (CI race detected)"
  exit 1
fi

echo "🧠 Running unified index builder..."

python3 << 'EOF'
import os
import json
import glob
import re
from pathlib import Path

ROOT = Path(os.getcwd())
SAL_FILE = ROOT / "semantic-salience.json"
OUTPUT_FILE = ROOT / "search-index.json"

# -------------------------------------------------------
# SAFE LOAD (no silent failures)
# -------------------------------------------------------

try:
    raw = SAL_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("semantic-salience.json is empty")

    salience = json.loads(raw)

except Exception as e:
    raise SystemExit(f"❌ Failed to load semantic-salience.json: {e}")

page_graph = salience.get("page_graph", {})
if not isinstance(page_graph, dict):
    raise SystemExit("❌ page_graph must be dict")

# -------------------------------------------------------
# BUILD CONCEPT MAP (in-memory, single pass)
# -------------------------------------------------------

concept_map = {}

for url, node in page_graph.items():
    concepts = []

    if isinstance(node, dict):
        raw = node.get("concepts", [])
        if isinstance(raw, list):
            for c in raw:
                if isinstance(c, str):
                    concepts.append(c)
                elif isinstance(c, dict):
                    w = c.get("word")
                    if w:
                        concepts.append(w)

    clean = []
    seen = set()

    for c in concepts:
        if not isinstance(c, str):
            continue
        c = c.strip().lower()
        if not c or c in seen:
            continue
        seen.add(c)
        clean.append(c)

    concept_map[url] = clean[:10]

# -------------------------------------------------------
# HTML DISCOVERY
# -------------------------------------------------------

html_files = [
    p for p in ROOT.rglob("*.html")
    if "/assets/" not in str(p)
]

# -------------------------------------------------------
# INDEX BUILD
# -------------------------------------------------------

index = {}

for file in sorted(html_files):
    rel = file.relative_to(ROOT)

    # URL normalization
    if str(rel) == "index.html":
        url = "https://unboundhealing.org/"
    else:
        url = str(rel).replace("index.html", "").replace(".html", "")
        url = "https://unboundhealing.org/" + url
        if not url.endswith("/"):
            url += "/"

    # TITLE
    html = file.read_text(errors="ignore")

    title_match = re.search(r"<title>(.*?)</title>", html, re.I)
    title = title_match.group(1).strip() if title_match else "Untitled"

    # DESCRIPTION
    desc_match = re.search(
        r'name="description"\s+content="(.*?)"',
        html,
        re.I
    )
    desc = desc_match.group(1).strip() if desc_match else ""

    # TAGS (direct lookup, no subprocess, no pipe)
    tags = concept_map.get(url, [])

    index[url] = {
        "title": title,
        "url": url,
        "path": str(file),
        "type": "page",
        "tags": ",".join(tags[:10]),
        "description": desc,
        "image": "",
        "last_modified": ""
    }

# -------------------------------------------------------
# ATOMIC WRITE (prevents CI partial writes)
# -------------------------------------------------------

tmp_path = OUTPUT_FILE.with_suffix(".tmp")

tmp_path.write_text(
    json.dumps(index, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

os.replace(tmp_path, OUTPUT_FILE)

print("✅ Search index built (v5 unified python builder)")
print(f"📦 pages indexed: {len(index)}")
print("🧠 semantic-salience is the single truth source")
EOF

echo "🎉 Done."
