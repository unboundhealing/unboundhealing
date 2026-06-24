import os
import json
import re
from bs4 import BeautifulSoup
from collections import Counter, defaultdict

ROOT = os.getcwd()
OUTPUT = "semantic-model.json"

# -----------------------------
# CONFIG
# -----------------------------
STOP = {
    "this","that","just","about","here","like","thing","things",
    "and","or","but","the","a","an","to","of","in","on","for","with","from"
}

MIN_WORD_LEN = 4
TOP_K = 15

# -----------------------------
# TEXT EXTRACTION
# -----------------------------
def extract_text(soup):
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    return soup.get_text(" ")

def tokenize(text):
    return re.findall(r"[a-zA-Z]{%d,}" % MIN_WORD_LEN, text.lower())

def normalize(word):
    return word.strip().lower()

# -----------------------------
# TONE MODEL (light field polarity)
# -----------------------------
def guess_tone(text):
    calm = ["presence", "listen", "quiet", "breath", "still", "aware", "simply", "gentle"]
    intense = ["urgent", "need", "must", "always", "never", "fix", "broken", "force"]

    t = text.lower()

    score = sum(t.count(w) for w in calm) - sum(t.count(w) for w in intense)

    if score > 2:
        return "contemplative"
    elif score < -2:
        return "intense"
    return "neutral"

# -----------------------------
# INTENT MODEL (structural gravity direction)
# -----------------------------
def infer_intent(title, text):
    t = (title + " " + text).lower()

    if "about" in t:
        return "identity"
    if "welcome" in t or "opening" in t:
        return "invitation"
    if "concept" in t:
        return "exploration"
    if "listen" in t:
        return "attention"
    return "reflection"

# -----------------------------
# BUILD MODEL
# -----------------------------
pages = []
global_freq = Counter()

# temporary per-page storage
page_tokens = {}

for root, _, files in os.walk("."):
    for file in files:
        if not file.endswith(".html"):
            continue

        path = os.path.join(root, file)

        try:
            with open(path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except:
            continue

        title = soup.title.string.strip() if soup.title else ""

        text = extract_text(soup)
        tokens = [normalize(t) for t in tokenize(text)]

        # filter noise
        tokens = [t for t in tokens if t not in STOP]

        if not tokens:
            continue

        freq = Counter(tokens)
        global_freq.update(freq)

        url = path.replace("./", "")
        url = url.replace("index.html", "")
        url = url.replace(".html", "")
        url = "https://unboundhealing.org/" + url

        page_tokens[url] = freq

        pages.append({
            "url": url,
            "title": title,
            "tone": guess_tone(text),
            "intent": infer_intent(title, text),
            "token_count": len(tokens)
        })

# -----------------------------
# BUILD WEIGHTED CONCEPT FIELD
# -----------------------------
model = {
    "pages": {},
    "concept_index": {},
    "edges": []
}

for page in pages:
    url = page["url"]
    freq = page_tokens[url]

    # top concepts per page (weighted)
    top = freq.most_common(TOP_K)

    concepts = []
    for word, count in top:
        global_weight = global_freq[word]

        # gravity weight = local importance × global resonance
        weight = (count / len(freq)) * (global_weight ** 0.5)

        concepts.append({
            "word": word,
            "weight": round(weight, 4)
        })

        # build global concept index
        if word not in model["concept_index"]:
            model["concept_index"][word] = {
                "global_count": global_weight,
                "pages": []
            }

        model["concept_index"][word]["pages"].append(url)

    model["pages"][url] = {
        "title": page["title"],
        "tone": page["tone"],
        "intent": page["intent"],
        "concepts": concepts
    }

# -----------------------------
# BUILD CROSS-PAGE GRAVITY EDGES
# -----------------------------
def overlap(a, b):
    sa = set(a)
    sb = set(b)
    shared = sa & sb
    return len(shared), list(shared)

urls = list(model["pages"].keys())

for i, u1 in enumerate(urls):
    for u2 in urls[i+1:]:

        c1 = [c["word"] for c in model["pages"][u1]["concepts"]]
        c2 = [c["word"] for c in model["pages"][u2]["concepts"]]

        score, shared = overlap(c1, c2)

        if score > 0:
            model["edges"].append({
                "from": u1,
                "to": u2,
                "weight": round(score, 3),
                "shared_concepts": shared
            })

# -----------------------------
# WRITE OUTPUT
# -----------------------------
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(model, f, indent=2, ensure_ascii=False)

print("🌌 Semantic gravity model built (v4.0 gravity-native)")
print("📦 pages:", len(model["pages"]))
print("📦 concepts:", len(model["concept_index"]))
print("📦 edges:", len(model["edges"]))
