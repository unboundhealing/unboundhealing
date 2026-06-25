#!/usr/bin/env python3

import os
import json
from pathlib import Path

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

HOME_INTEL = os.path.join(ROOT, "homepage-intelligence.json")


# =========================================================
# LOADERS
# =========================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# URL LABEL HELPERS
# =========================================================

def prettify_url(url):
    """
    Convert:
    https://unboundhealing.org/opening/this-morning/

    into:

    This Morning
    """

    if not url:
        return "Untitled"

    path = (
        url.replace("https://unboundhealing.org", "")
        .strip("/")
    )

    if not path:
        return "Home"

    slug = path.split("/")[-1]

    return slug.replace("-", " ").title()


# =========================================================
# HOMEPAGE RENDERER
# =========================================================

def render_homepage(intel):

    data = intel.get("homepage_intelligence", {})

    concepts = data.get("top_concepts", [])
    hubs = data.get("top_hubs", [])

    concepts_html = "".join(
        f'<span class="chip">{c["concept"]}</span>'
        for c in concepts
    )

    hubs_html = "".join(
        f'''
<a class="chip" href="{h["node"]}">
  {prettify_url(h["node"])}
</a>
'''
        for h in hubs
    )

    return f"""
<section class="homepage-intelligence">

  <h3>Arising Concepts</h3>

  <div class="chip-cloud">
    {concepts_html}
  </div>

  <h3>Structural Hubs</h3>

  <div class="chip-cloud">
    {hubs_html}
  </div>

</section>
""".strip()


# =========================================================
# HOMEPAGE DETECTION
# =========================================================

def is_root_homepage(path: Path) -> bool:
    """
    ONLY inject into the actual site homepage.

    Prevents accidental injection into:

        opening/index.html
        concept/index.html
        etc.
    """

    return path.resolve() == Path(ROOT, "index.html").resolve()


# =========================================================
# INJECTOR
# =========================================================

def inject(html, block):
    return html.replace(
        '<div id="homepage-intelligence"></div>',
        block
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not os.path.exists(HOME_INTEL):
        raise FileNotFoundError(
            f"Missing homepage intelligence file:\n{HOME_INTEL}"
        )

    homepage_intel = load_json(HOME_INTEL)

    homepage_block = render_homepage(homepage_intel)

    injected = 0

    for path in Path(ROOT).rglob("*.html"):

        if not is_root_homepage(path):
            continue

        html = path.read_text(encoding="utf-8")

        if '<div id="homepage-intelligence"></div>' not in html:
            print("⚠️ homepage placeholder missing:", path)
            continue

        html = inject(html, homepage_block)

        path.write_text(html, encoding="utf-8")

        injected += 1
        print("🏠 injected homepage intelligence:", path)

    print()
    print("========================")
    print("HOMEPAGE INJECTION COMPLETE")
    print("PAGES UPDATED:", injected)


if __name__ == "__main__":
    main()
