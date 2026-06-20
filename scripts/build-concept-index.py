import json
import os

ROOT = os.environ.get(“GITHUB_WORKSPACE”, os.getcwd())

CLUSTERS_FILE = os.path.join(
ROOT,
“concept-clusters.json”
)

SALIENCE_FILE = os.path.join(
ROOT,
“semantic-salience.json”
)

OUTPUT = os.path.join(
ROOT,
“concept-index.json”
)

–––––––––––––––––

Load

–––––––––––––––––

with open(CLUSTERS_FILE, “r”, encoding=“utf-8”) as f:
clusters = json.load(f)

with open(SALIENCE_FILE, “r”, encoding=“utf-8”) as f:
salience = json.load(f)

–––––––––––––––––

Build concept index

–––––––––––––––––

index = {}

for concept, pages in clusters.items():

concept_key = concept.strip().lower()
index[concept_key] = {
    "salience": salience.get(
        concept_key,
        0
    ),
    "pages": pages
}

–––––––––––––––––

Write

–––––––––––––––––

with open(
OUTPUT,
“w”,
encoding=“utf-8”
) as f:

json.dump(
    index,
    f,
    indent=2,
    ensure_ascii=False
)

print(“🗂 Building concept index…”)
print(“🗂 Concept index built”)
print(“📦 Wrote:”, OUTPUT)