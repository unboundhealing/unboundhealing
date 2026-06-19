import json
import os

# -----------------------------
# Paths
# -----------------------------
ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")
LABEL_FILE = os.path.join(ROOT, "homepage-ui-labels.json")

INCLUDES_DIR = os.path.join(ROOT, "_includes")
OUTPUT = os.path.join(INCLUDES_DIR, "homepage-intelligence-blocks.html")

# -----------------------------
# Ensure output directory exists
# -----------------------------
os.makedirs(INCLUDES_DIR, exist_ok=True)

# -----------------------------
# Safe JSON loader
# -----------------------------
def safe_load_json(path, fallback=None):
    if not os.path.exists(path):
        return fallback or {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return fallback or {}

intel = safe_load_json(INTEL_FILE, {})
labels = safe_load_json(LABEL_FILE, {
    "featured": "Points of attention",
    "concepts": "Fields of meaning"
})

# -----------------------------
# Helpers
# -----------------------------
def clean_url(url):
    if not url:
        return "#"
    return url.replace("https://unboundhealing.org", "").rstrip("/")

# -----------------------------
# Build HTML safely
# -----------------------------
html = []

html.append("""
<!-- ========================= -->
<!-- HOMEPAGE INTELLIGENCE UI -->
<!-- v3.3 Phase 4 -->
<!-- ========================= -->
""")

# =============================
# POINTS OF ATTENTION
# =============================
featured = intel.get("featured_pages", [])

html.append(f"""
<section class="homepage-section points-of-attention">
  <h2>{labels.get("featured", "Points of attention")}</h2>
  <ul>
""")

if featured:
    for page in featured[:5]:
        url = clean_url(page.get("url"))
        label = url.strip("/") or "/"
        html.append(f'    <li><a href="{url}">{label}</a></li>')
else:
    html.append('    <li class="empty">No featured pages yet</li>')

html.append("""
  </ul>
</section>
""")

# =============================
# FIELDS OF MEANING
# =============================
concepts = intel.get("top_concepts", [])

html.append(f"""
<section class="homepage-section fields-of-meaning">
  <h2>{labels.get("concepts", "Fields of meaning")}</h2>
  <ul>
""")

if concepts:
    for concept in concepts[:8]:
        name = concept.get("concept", "unknown")
        html.append(f'    <li>{name}</li>')
else:
    html.append('    <li class="empty">No conceptual structure yet</li>')

html.append("""
  </ul>
</section>
""")

# -----------------------------
# WRITE OUTPUT
# -----------------------------
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print("🏠 Homepage HTML blocks rendered (Phase 4 safe v3.3)")
