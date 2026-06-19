import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")
LABEL_FILE = os.path.join(ROOT, "homepage-ui-labels.json")
TITLES_FILE = os.path.join(ROOT, "page-titles.json")

OUTPUT = os.path.join(ROOT, "assets", "homepage-intelligence-blocks.html")

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)


def safe_load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def clean_url(url):
    if not url:
        return "#"
    return url.replace("https://unboundhealing.org", "").rstrip("/")


def normalize_url_key(url):
    if not url:
        return "/"
    url = url.replace("https://unboundhealing.org", "")
    url = "/" + url.strip("/") + "/"
    return "/" if url == "//" else url


def make_chip(label, href=None, css_class="chip"):
    if href:
        return f'<a class="{css_class}" href="{href}">{label}</a>'
    return f'<span class="{css_class}">{label}</span>'


intel = safe_load_json(INTEL_FILE)
labels_raw = safe_load_json(LABEL_FILE)
titles = safe_load_json(TITLES_FILE)

labels = {
    "featured": labels_raw.get("featured", "Arising observations..."),
    "concepts": labels_raw.get("concepts", "Essential inspirations...")
}

featured = intel.get("featured_pages", [])[:3]
concepts = intel.get("concept_clusters", [])[:3]

html = []

# =========================
# ARISEN OBSERVATIONS (UNIFIED CHIPS)
# =========================
html.append(f"""
<section class="arising-observations">
  <h2>{labels["featured"]}</h2>
  <div class="chip-cloud">
""")

if featured:
    for page in featured:
        raw_url = page.get("url")
        url = clean_url(raw_url)

        key = normalize_url_key(raw_url)
        title = titles.get(key)

        if not title:
            title = url.strip("/").replace("-", " ").title()

        html.append(make_chip(title, url))
else:
    html.append('<span class="chip muted">No featured pages found</span>')

html.append("""
  </div>
</section>
""")

# =========================
# ESSENTIAL INSPIRATIONS (UNIFIED CHIPS)
# =========================
html.append(f"""
<section class="essential-inspirations">
  <h2>{labels["concepts"]}</h2>
  <div class="chip-cloud">
""")

if concepts:
    for c in concepts:
        concept = c.get("concept", "unknown")
        html.append(make_chip(concept))
else:
    html.append('<span class="chip muted">No concepts found</span>')

html.append("""
  </div>
</section>
""")

# =========================
# WRITE OUTPUT
# =========================
final_html = "\n".join(html)

tmp_output = OUTPUT + ".tmp"
with open(tmp_output, "w", encoding="utf-8") as f:
    f.write(final_html)

os.replace(tmp_output, OUTPUT)

print("🏠 Homepage intelligence rendered (unified chip system)")
print("OUTPUT PATH:", OUTPUT)
print("OUTPUT PATH:", OUTPUT)
print("OUTPUT SIZE:", len(final_html))
