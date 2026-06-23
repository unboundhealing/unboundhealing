#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry (v3 hardened + fully JSON-safe)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"

# ---------------------------------------------------
# STEP 1 — DISCOVER FILES (DETERMINISTIC)
# ---------------------------------------------------

echo "📂 scanning root: $(pwd)"

mapfile -t RAW_FILES < <(
  find . -type f -name "*.html" \
    ! -path "./.git/*" \
    ! -path "./.github/*" \
    ! -path "./scripts/*" \
    | sort
)

echo "📦 html files discovered: ${#RAW_FILES[@]}"

if [ "${#RAW_FILES[@]}" -eq 0 ]; then
  echo "❌ registry scan returned ZERO HTML files"
  echo "💡 check CI checkout path / working directory"
  exit 1
fi

# ---------------------------------------------------
# STEP 2 — BUILD JSON SAFELY (PYTHON-EMITTED)
# ---------------------------------------------------

echo "🧠 building JSON registry (safe serializer)..."

python3 - <<'EOF' > "$TMP"
import json
import os

files = os.environ.get("RAW_FILES_LIST", "").split("\n")
files = [f for f in files if f.strip()]

pages = []

for f in files:
    clean = f.lstrip("./")

    # skip empty safety
    if not clean:
        continue

    # canonical URL transform
    url_path = clean
    if url_path.endswith("index.html"):
        url_path = url_path[:-10]
    elif url_path.endswith(".html"):
        url_path = url_path[:-5]

    url_path = url_path.lstrip("./")

    url = "https://unboundhealing.org/" + url_path

    # normalize double slashes safely
    url = url.replace("https://unboundhealing.org//", "https://unboundhealing.org/")

    page_type = "asset" if clean.startswith("assets/") else "page"

    pages.append({
        "path": clean,
        "url": url,
        "type": page_type
    })

print(json.dumps({"pages": pages}, indent=2))
EOF

# pass file list safely into python (newline separated)
RAW_FILES_LIST="$(printf "%s\n" "${RAW_FILES[@]}")" python3 - <<'EOF' > "$TMP"
import json, os

files = os.environ.get("RAW_FILES_LIST", "").split("\n")
files = [f for f in files if f.strip()]

pages = []

for f in files:
    clean = f.lstrip("./")

    if not clean:
        continue

    url_path = clean
    if url_path.endswith("index.html"):
        url_path = url_path[:-10]
    elif url_path.endswith(".html"):
        url_path = url_path[:-5]

    url_path = url_path.lstrip("./")
    url = "https://unboundhealing.org/" + url_path
    url = url.replace("https://unboundhealing.org//", "https://unboundhealing.org/")

    page_type = "asset" if clean.startswith("assets/") else "page"

    pages.append({
        "path": clean,
        "url": url,
        "type": page_type
    })

print(json.dumps({"pages": pages}, indent=2))
EOF

# ---------------------------------------------------
# STEP 3 — VALIDATE JSON (HARD FAIL SAFE)
# ---------------------------------------------------

echo "🧪 validating registry..."

python3 - <<EOF
import json
with open("$TMP","r") as f:
    data = json.load(f)

assert "pages" in data
assert isinstance(data["pages"], list)

print("✅ registry valid")
print("📦 pages:", len(data["pages"]))
EOF

# ---------------------------------------------------
# STEP 4 — ATOMIC WRITE
# ---------------------------------------------------

mv "$TMP" "$OUTPUT"

echo "📁 wrote: $OUTPUT"
echo "✅ content registry built (v3 deterministic + fully JSON-safe)"
