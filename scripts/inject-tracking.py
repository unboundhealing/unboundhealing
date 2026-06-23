import os
from bs4 import BeautifulSoup

# =========================================================
# ROOT
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

# =========================================================
# TRACKING ASSET (CONFIGURATION, NOT TRUTH)
# =========================================================

TRACKER_PATH = os.environ.get(
    "SEMANTIC_TRACKER_PATH",
    "/assets/js/semantic-tracker.js"
)


# =========================================================
# FILE DISCOVERY
# =========================================================

def find_html_files():
    """
    Pure structural scan.
    No semantic interpretation.
    No graph dependency.
    """

    files = []

    for root, _, fns in os.walk(ROOT):

        # skip asset pipeline entirely
        if "/assets/" in root.replace("\\", "/"):
            continue

        for f in fns:
            if f.endswith(".html"):
                files.append(os.path.join(root, f))

    return files


# =========================================================
# TRACKING INJECTION (IDEMPOTENT SIDE EFFECT)
# =========================================================

def inject_tracking_script(soup):
    """
    PURE SIDE EFFECT:

    - no salience dependency
    - no graph dependency
    - no page intelligence dependency
    """

    # ---------------------------------------------
    # HARD IDEMPOTENCY CHECK
    # ---------------------------------------------
    existing = soup.find("script", {"src": TRACKER_PATH})

    if existing:
        return

    script = soup.new_tag("script", src=TRACKER_PATH)
    script["defer"] = True

    # ---------------------------------------------
    # SAFE INSERTION STRATEGY
    # ---------------------------------------------
    if soup.body:
        soup.body.append(script)
    elif soup.head:
        soup.head.append(script)
    else:
        soup.append(script)


# =========================================================
# PROCESSOR (EXPLICIT ENTRYPOINT)
# =========================================================

def process_file(file_path):
    """
    Isolated per-file operation for:
    - CI safety
    - future parallelization
    - testability
    """

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        inject_tracking_script(soup)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

        print(f"📡 Injected tracker into {file_path}")

    except Exception as e:
        print(f"⚠️ Skipped {file_path}: {e}")


# =========================================================
# ENTRYPOINT
# =========================================================

def main():

    html_files = find_html_files()

    for file_path in html_files:
        process_file(file_path)

    print("✅ Tracking injection complete (v4 consumer-safe, no-truth coupling)")


if __name__ == "__main__":
    main()
