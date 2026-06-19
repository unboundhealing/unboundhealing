import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")
LABEL_FILE = os.path.join(ROOT, "homepage-ui-labels.json")
OUTPUT = os.path.join(ROOT, "homepage-intelligence-blocks.html")

# -----------------------------
# Load data
# -----------------------------
with open(INTEL_FILE, "r", encoding="utf-8") as f:
    intel = json.load(f)

with open(LABEL_FILE, "r", encoding="utf-8") as f:
    labels = json.load(f)

# -----------------------------
# Helpers
# -----------------------------
def clean_url(url):
    return url.replace("https://unboundhealing.org", "")

# -----------------------------
# Build HTML
# -----------------------------
html = []

# =============================
# POINTS OF ATTENTION
# =============================
html.append(f"""
<section class="homepage-section points-of-attention">
  <h2>{labels.get("featured", "Points of attention")}</h2>
  <ul>
""")

for page in intel.get("featured_pages", [])[:5]:
    url = clean_url(page["url"])
    html.append(f'    <li><a href="{url}">{url.strip("/")}</a></li>')

html.append("""
  </ul>
</section>
""")

# =============================
# FIELDS OF MEANING
# =============================
html.append(f"""
<section class="homepage-section fields-of-meaning">
  <h2>{labels.get("concepts", "Fields of meaning")}</h2>
  <ul>
""")

for concept in intel.get("concept_clusters", [])[:8]:
    name = concept["concept"]
    html.append(f'    <li>{name}</li>')

html.append("""
  </ul>
</section>
""")

# -----------------------------
# WRITE OUTPUT
# -----------------------------
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print("🏠 Homepage HTML blocks rendered (Phase 4)")
