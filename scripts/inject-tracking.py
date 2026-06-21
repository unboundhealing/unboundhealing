import os
from bs4 import BeautifulSoup

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

TRACKER_PATH = "/assets/js/semantic-tracker.js"


# -----------------------------
# Helpers
# -----------------------------
def find_html_files():
    files = []

    for root, _, fns in os.walk(ROOT):

        # skip asset pipeline completely
        if "/assets/" in root.replace("\\", "/"):
            continue

        for f in fns:
            if f.endswith(".html"):
                files.append(os.path.join(root, f))

    return files


# -----------------------------
# Injection
# -----------------------------
def inject_tracking_script(soup):
    """
    Idempotent tracking injection
    """

    # avoid duplicate injection
    if soup.find("script", {"src": TRACKER_PATH}):
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True

    if soup.body:
        soup.body.append(script)
    else:
        soup.append(script)


# -----------------------------
# Main
# -----------------------------
HTML_FILES = find_html_files()

for file in HTML_FILES:

    try:
        with open(file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        inject_tracking_script(soup)

        with open(file, "w", encoding="utf-8") as f:
            f.write(str(soup))

        print(f"📡 Injected tracker into {file}")

    except Exception as e:
        print(f"⚠️ Skipped {file}: {e}")

print("✅ Tracking injection complete")
