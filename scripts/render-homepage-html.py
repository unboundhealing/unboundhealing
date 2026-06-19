import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")
LABEL_FILE = os.path.join(ROOT, "homepage-ui-labels.json")

OUTPUT = os.path.join(ROOT, "assets", "homepage-intelligence-blocks.html")

# 🔥 ENSURE OUTPUT DIRECTORY EXISTS (CRITICAL)
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

def safe_load_json(path, fallback=None):
    if not os.path.exists(path):
        return fallback or {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

intel = safe_load_json(INTEL_FILE, {})
labels = safe_load_json(LABEL_FILE, {
    "featured": "Points of attention",
    "concepts": "Fields of meaning"
})

print("INTEL RAW:", intel)

def clean_url(url):
    return url.replace("https://unboundhealing.org", "").rstrip("/")

featured = intel.get("featured_pages", [])
concepts = intel.get("concept_clusters", [])

html = []

# =============================
# HARD VISIBILITY MARKER (ALWAYS SHOW)
# =============================
html.append("""
<section style="padding:10px;background:#fff3cd;border:1px solid #ffeeba;">
  <strong>INTELLIGENCE SYSTEM ACTIVE</strong>
  <div>featured_pages: {}</div>
  <div>concept_clusters: {}</div>
</section>
""".format(len(featured), len(concepts)))

# =============================
# FEATURED
# =============================
html.append("<section class='points-of-attention'><h2>{}</h2><ul>".format(labels["featured"]))

if featured:
    for page in featured[:5]:
        url = clean_url(page.get("url", "#"))
        html.append(f'<li><a href="{url}">{url}</a></li>')
else:
    html.append("<li>No featured pages found</li>")

html.append("</ul></section>")

# =============================
# CONCEPTS
# =============================
html.append("<section class='fields-of-meaning'><h2>{}</h2><ul>".format(labels["concepts"]))

if concepts:
    for c in concepts[:8]:
        html.append(f'<li>{c.get("concept","unknown")}</li>')
else:
    html.append("<li>No concepts found</li>")

html.append("</ul></section>")

# =============================
# WRITE OUTPUT (FORCE FLUSHED CONTENT)
# =============================
final_html = "\n".join(html)

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(final_html)

print("OUTPUT PATH:", OUTPUT)
print("OUTPUT SIZE:", len(final_html))
print("🏠 Homepage intelligence HTML rendered (FIXED TEST VERSION)")
