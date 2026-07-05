#!/usr/bin/env python3

import json
import os
from pathlib import Path

# =========================================================
# ROOT / INPUT / OUTPUT
# =========================================================

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))

SAL_FILE = ROOT / "assets/semantic-salience.json"
ALIASES_FILE = ROOT / "assets/semantic-aliases.json"
OUTPUT_FILE = ROOT / "assets/vocabulary.json"

# =========================================================
# LOAD
# =========================================================

def load_json(path):
    try:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            raise ValueError("empty file")
        return json.loads(raw)
    except Exception as e:
        raise SystemExit(f"❌ Failed to load {path}: {e}")

# =========================================================
# LOAD SEMANTIC ALIASES
# =========================================================

def load_aliases():
    if not ALIASES_FILE.exists():
        return {}

    try:
        return json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

# =========================================================
# NORMALIZE TAGS
# =========================================================

def normalize_tag(tag):
    if not isinstance(tag, str):
        return None
    tag = tag.strip().lower()
    return tag if tag else None

# =========================================================
# GENERATED ALIASES
# =========================================================

def generate_aliases(tags, semantic_aliases):

    aliases = set()

    for tag in tags:

        # structural aliases
        parts = tag.split("-")
        if len(parts) > 1:
            aliases.add(" ".join(parts))

        parts = tag.split("_")
        if len(parts) > 1:
            aliases.add(" ".join(parts))

        # semantic aliases
        for alias in semantic_aliases.get(tag, []):
            aliases.add(normalize_tag(alias))

    aliases -= set(tags)

    return sorted(a for a in aliases if a)

# =========================================================
# MAIN
# =========================================================

def main():

    salience = load_json(SAL_FILE)
    semantic_aliases = load_aliases()
    
    nodes = salience.get("nodes", {})
    if not isinstance(nodes, dict):
        raise SystemExit("❌ nodes must be dict")

    tags_index = {}

    for url, node in nodes.items():

        if not isinstance(node, dict):
            continue

        raw = node.get("concepts", [])
        if not isinstance(raw, list):
            continue

        seen = set()
        cleaned = []

        for t in raw:
            t = normalize_tag(t)
            if not t or t in seen:
                continue
            seen.add(t)
            cleaned.append(t)

        tags = cleaned[:10]
        aliases = generate_aliases(tags, semantic_aliases)

        if url == "https://unboundhealing.org/":
            print("🏠 ROOT TAGS:", tags)
            print("🏠 ROOT ALIASES:", aliases)
            
        tags_index[url] = {
            "version": 2,
            "generated": True,
            "tags": tags,
            "aliases": aliases,
        }

    # =====================================================
    # WRITE (atomic)
    # =====================================================

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    tmp = OUTPUT_FILE.with_suffix(".tmp")

    tmp.write_text(
        json.dumps(tags_index, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    os.replace(tmp, OUTPUT_FILE)

    print("✅ Vocabulary built")
    print(f"📦 vocabulary entries: {len(tags_index)}")

# =========================================================

if __name__ == "__main__":
    main()
