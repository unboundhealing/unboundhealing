import os
from bs4 import BeautifulSoup

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

TRACKER_PATH = "/assets/js/semantic-tracker.js"

def find_html_files():
    files = []
    for root, _, fns in os.walk(ROOT):
        for f in fns:
            if f.endswith(".html"):
                files.append(os.path.join(root, f))
    return files


HTML_FILES = find_html_files()

for file in HTML_FILES:

    try:
        with open(file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # avoid duplicate injection
        if soup.find("script", {"src": TRACKER_PATH}):
            continue

        script = soup.new_tag("script", src=TRACKER_PATH)
        script["defer"] = True

        if soup.body:
            soup.body.append(script)
        else:
            soup.append(script)

        with open(file, "w", encoding="utf-8") as f:
            f.write(str(soup))

        print(f"📡 Injected tracker into {file}")

    except Exception as e:
        print(f"⚠️ Skipped {file}: {e}")

print("✅ Tracking injection complete")
