#!/usr/bin/env python3

import os
import json
from pathlib import Path

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

HOME_INTEL = os.path.join(ROOT, "homepage-intelligence.json")
SAL_FILE = os.path.join(ROOT, "semantic-salience.json")


# =========================================================
# LOADERS
# =========================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# HOMEPAGE RENDERER
# =========================================================

def render_homepage(intel):
    data = intel["homepage_intelligence"]

    concepts = data["top_concepts"]
    hubs = data["top_hubs"]

    concepts_html = "".join(
        f'<span class="chip">{c["concept"]}</span>'
        for c in concepts
    )

    hubs_html = "".join(
        f'<span class="chip">{h["node"]}</span>'
        for h in hubs
    )

    return f"""
<section class="intelligence homepage-intelligence">

  <h2>Arising Concepts</h2>
  <div class="chip-cloud">
    {concepts_html}
  </div>

  <h2>Structural Hubs</h2>
  <div class="chip-cloud">
    {hubs_html}
  </div>

</section>
"""


# =========================================================
# RELATED CONTENT RENDERER (ARTICLE PAGES)
# =========================================================

def render_related(salience):
    sal = salience["salience"]

    # top concepts by frequency
    top = sorted(
        sal.items(),
        key=lambda x: -(x[1]["frequency"] + x[1]["connectivity"])
    )[:10]

    chips = "".join(
        f'<span class="chip">{c[0]}</span>'
        for c in top
    )

    return f"""
<section class="related-content">

  <h2>Related</h2>

  <div class="chip-cloud">
    {chips}
  </div>

</section>
"""


# =========================================================
# PAGE TYPE DETECTION
# =========================================================

def is_homepage(path: str) -> bool:
    return path.endswith("index.html") or path == "index.html"


def inject(html: str, block: str, selector: str) -> str:
    return html.replace(selector, block)


# =========================================================
# MAIN INJECTOR
# =========================================================

def main():

    homepage_intel = load_json(HOME_INTEL)
    salience = load_json(SAL_FILE)

    home_block = render_homepage(homepage_intel)
    related_block = render_related(salience)

    for path in Path(ROOT).rglob("*.html"):

        html = path.read_text(encoding="utf-8")

        if is_homepage(str(path)):
            if '<div id="homepage-intelligence"></div>' in html:
                new_html = inject(
                    html,
                    home_block,
                    '<div id="homepage-intelligence"></div>'
                )
                path.write_text(new_html, encoding="utf-8")
                print("🏠 injected homepage:", path)

        else:
            if '<div class="related-content"></div>' in html:
                new_html = inject(
                    html,
                    related_block,
                    '<div class="related-content"></div>'
                )
                path.write_text(new_html, encoding="utf-8")
                print("🔗 injected related:", path)


if __name__ == "__main__":
    main()
