#!/usr/bin/env python3

import os
import re
import json
from collections import defaultdict
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# =========================================================
# CONFIG — SINGLE TRUTH CONTEXT
# =========================================================

DOMAIN = "https://unboundhealing.org/"

STOPWORDS = {
    "https", "http", "www",
    "com", "org",
    "html", "indexhtml", "index"
}

# =========================================================
# CANONICALIZATION (STRUCTURAL NORMALIZATION ONLY)
# =========================================================

def canonicalize_concept(text: str) -> str:
    """
    Enforces a single stable representation for concepts.

    RULE:
    - spaces, underscores, hyphens collapse into hyphen form
    - lowercase normalization
    - structural consistency only (NOT semantic interpretation)
    """

    text = text.lower().strip()

    # unify separators into hyphen
    text = re.sub(r"[\s_]+", "-", text)

    # remove invalid characters
    text = re.sub(r"[^a-z0-9\-]", "", text)

    # collapse multiple hyphens
    text = re.sub(r"-{2,}", "-", text)

    return text

# =========================================================
# DISPLAY TITLE
# =========================================================

def get_display_title(node, url=None):
    if not node:
        return ""

    title = node.get("title")

    if isinstance(title, str) and title.strip():
        return title.strip()

    url = url or node.get("url", "")

    if not url:
        return ""

    slug = url.rstrip("/").split("/")[-1]

    return slug if slug else ""

# -------------------------------------------------------
# SECTION
# -------------------------------------------------------

def get_section(url):

    path = url.replace("https://unboundhealing.org/", "").strip("/")

    if path == "":
        return "home"

    return path.split("/")[0]

# -------------------------------------------------------
# KIND
# -------------------------------------------------------

def get_kind(section):

    mapping = {
        "home": "home",
        "opening": "journal", 
        "welcome": "journal",
        "concept": "concept",
        "about": "about",
        "gathering": "gathering",
        "supporting": "supporting",
        "listen": "listen"
    }

    section = (section or "").strip().lower()
    return mapping.get(section, "page")
    
# -------------------------------------------------------
# BUILD SEARCH TEXT
# -------------------------------------------------------

def build_search_text(
    title,
    description,
    kind,
    excerpt,
    tags,
    concepts,
    aliases=None,
):
    aliases = aliases or []
    
    fields = [
        title,
        description,
        kind,
        excerpt,
        " ".join(tags),
        " ".join(concepts),
        " ".join(aliases),
    ]

    return " ".join(
        str(x).strip().lower()
        for x in fields
        if x
    )
    
# =========================================================
# NORMALIZATION (RAW STRUCTURAL CLEANING)
# =========================================================

def normalize(text: str) -> str:
    """
    Normalize raw structural input into token space.
    """

    text = text.lower()

    text = re.sub(r"\.html?$", "", text)

    text = re.sub(r"[^a-z0-9/_\-\s]", "", text)

    return text


# =========================================================
# CONCEPT EXTRACTION (STRUCTURAL REALITY + LIGHT PHRASES)
# =========================================================

def extract_concepts(path: str):
    """
    Extract concepts from structural reality.

    SOURCES:
    - URL/path structure
    - token segmentation
    - phrase adjacency

    IMPORTANT:
    Canonicalization is applied BEFORE storage.
    """

    base = normalize(path)

    tokens = [
        t for t in re.split(r"[/_\-\s]+", base)
        if t and t not in STOPWORDS
    ]

    raw_concepts = []

    # -----------------------------
    # 1. single-token concepts
    # -----------------------------
    for t in tokens:
        raw_concepts.append(t)

    # -----------------------------
    # 2. phrase concepts (2-token)
    # -----------------------------
    for i in range(len(tokens) - 1):
        raw_concepts.append(f"{tokens[i]} {tokens[i+1]}")

    # -----------------------------
    # 3. phrase concepts (3-token)
    # -----------------------------
    for i in range(len(tokens) - 2):
        raw_concepts.append(f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}")

    # -----------------------------
    # CANONICALIZATION STEP
    # -----------------------------
    seen = set()
    concepts = []

    for c in raw_concepts:
        canon = canonicalize_concept(c)

        if not canon:
            continue

        if canon not in seen:
            seen.add(canon)
            concepts.append(canon)

    return concepts


# =========================================================
# URL RESOLUTION
# =========================================================

def build_url(path: str) -> str:

    path = path.replace("\\", "/")

    if path.endswith("index.html"):
        path = path[:-10]
    elif path.endswith(".html"):
        path = path[:-5]

    return urljoin(DOMAIN, path.lstrip("/"))

def canonicalize_url(url: str) -> str:
    if not isinstance(url, str):
        return ""

    url = url.strip()

    if not url.startswith("http"):
        return ""

    # collapse accidental duplicate slashes (except protocol)
    url = re.sub(r"([^:])/+", r"\1/", url)

    # remove trailing slash, re-add single consistent one
    url = url.rstrip("/")
    return url + "/"


# =========================================================
# PAGE METADATA EXTRACTION
# =========================================================

def extract_page_metadata(full_path, url):
    """
    Extract real HTML metadata for truth-aligned rendering.
    """

    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # -----------------------------
        # TITLE
        # Prefer <h1>, then <title>
        # -----------------------------
        title = ""

        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(" ", strip=True)

            # remove decorative parentheses used in rendered titles
            title = re.sub(r"^\(+|\)+$", "", title).strip()

        if not title:
            title_tag = soup.find("title")
            if title_tag and title_tag.text:
                title = title_tag.text.strip()

                # remove site suffix
                title = re.sub(
                    r"\s*\|\s*Unbound Healing Ministries\s*$",
                    "",
                    title,
                    flags=re.I,
                ).strip()
    
        # -----------------------------
        # DESCRIPTION
        # -----------------------------
        desc = ""

        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            desc = meta.get("content", "").strip()

        # -----------------------------
        # WORD COUNT + EXCERPT
        # ----------------------
        main = soup.find("main")

        text = main.get_text(" ", strip=True) if main else soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()

        words = re.findall(r"\b\w+\b", text.lower())
        word_count = len(words)

        

        section = get_section(url)
        kind = get_kind(section)
        excerpt = " ".join(text.split()[:60])

        search_text = build_search_text(
            title,
            desc,
            kind,
            excerpt,
            tags,
            concepts,
            []
        )

        return {
            "title": title,
            "description": desc,
            "kind": kind,
            "excerpt": excerpt,
            "search_text": search_text,
            "word_count": word_count
        }
        
    except Exception as e:
        print("⚠️ metadata extraction failed:", e)
        return {
            "title": "",
            "description": "",
            "kind": "",
            "excerpt": "",
            "search_text": "",
            "word_count": 0,
    }
            
# =========================================================
# REGISTRY (STRUCTURAL REALITY INDEX)
# =========================================================

def build_registry(root, html_files):
    registry = {}

    for path in html_files:

        full_path = os.path.join(root, path)

        metadata = extract_page_metadata(full_path, url)
        url = canonicalize_url(build_url(path))
        concepts = extract_concepts(path)    

        registry[url] = {
            "path": path,
            "url": url,
            "title": metadata["title"].strip(),   # <-- ADD THIS (critical)
            "description": metadata["description"],
            "kind": metadata["kind"],
            "excerpt": metadata["excerpt"],
            "search_text": metadata["search_text"],
            "concepts": concepts,
            "word_count": metadata["word_count"]
        }

    return registry


# =========================================================
# GRAPH = STRUCTURE OF REALITY
# =========================================================

def build_graph(registry):
    """
    GRAPH = STRUCTURE ONLY

    - nodes = existence
    - edges = co-occurrence
    """

    nodes = {}
    edge_weights = defaultdict(int)

    for url, data in registry.items():

        nodes[url] = {
            "path": data["path"],
            "url": data["url"],
            "title": data["title"],
            "description": data["description"],
            "kind": data["kind"],
            "excerpt": data["excerpt"],
            "search_text": data["search_text"],
            "concepts": data.get("concepts", []),
            "word_count": data.get("word_count", 0)
        }
        
        concepts = data["concepts"]

        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):

                a = concepts[i]
                b = concepts[j]

                key = tuple(sorted((a, b)))
                edge_weights[key] += 1

    edges = [
        {"a": a, "b": b, "weight": w}
        for (a, b), w in edge_weights.items()
    ]

    return nodes, edges


# =========================================================
# SALIENCE = WEIGHTING SIGNALS ONLY (NO RANKING)
# =========================================================

def build_salience(registry, edges):
    """
    SALIENCE = observable signals only
    """

    frequency = defaultdict(int)
    connectivity = defaultdict(int)

    search_signal = defaultdict(int)
    excerpt_signal = defaultdict(int)
    word_signal = defaultdict(int)

    # ----------------------------------------------------
    # concept frequency (existing)
    # ----------------------------------------------------
    for page in registry.values():
        for concept in page["concepts"]:
            frequency[concept] += 1

        # ------------------------------------------------
        # NEW: text-based signals per page
        # ------------------------------------------------

        text = page.get("search_text", "")
        excerpt = page.get("excerpt", "")
        wc = page.get("word_count", 0)

        # crude tokenization (intentionally lightweight)
        text_tokens = set(text.split())
        excerpt_tokens = set(excerpt.split())

        for concept in page["concepts"]:
            ct = concept.lower()

            # search_text reinforcement
            if ct in text_tokens:
                search_signal[ct] += 2
            else:
                search_signal[ct] += 0

            # excerpt reinforcement (lighter)
            if ct in excerpt_tokens:
                excerpt_signal[ct] += 1

            # word count signal (normalize banding)
            if wc > 150:
                word_signal[ct] += 2
            elif wc > 50:
                word_signal[ct] += 1

    # ----------------------------------------------------
    # connectivity (existing)
    # ----------------------------------------------------
    neighbors = defaultdict(set)

    for edge in edges:
        a = edge["a"]
        b = edge["b"]
        neighbors[a].add(b)
        neighbors[b].add(a)

    for concept, neigh in neighbors.items():
        connectivity[concept] = len(neigh)

    # ----------------------------------------------------
    # FINAL SALIENCE OBJECT
    # ----------------------------------------------------
    salience = {}
    all_concepts = set(frequency) | set(connectivity)

    for c in all_concepts:
        salience[c] = {
            "frequency": frequency[c],
            "connectivity": connectivity[c],

            # NEW SIGNALS
            "search_signal": search_signal[c],
            "excerpt_signal": excerpt_signal[c],
            "word_signal": word_signal[c],
        }

    return salience


# =========================================================
# PAGE COMPARISON ENGINE
# =========================================================

def token_overlap(a, b):

    if not a or not b:
        return 0

    ta = set(a.lower().split())
    tb = set(b.lower().split())

    return len(ta & tb)

def concept_overlap(a, b):

    ca = set(a.get("concepts", []))
    cb = set(b.get("concepts", []))

    return len(ca & cb)

def word_similarity(a, b):

    wa = a.get("word_count", 0)
    wb = b.get("word_count", 0)

    if wa == 0 and wb == 0:
        return 0

    return 1 - abs(wa - wb) / max(wa, wb)

def compare_pages(page_a, page_b):

    concept = len(set(page_a.get("concepts", [])) & set(page_b.get("concepts", [])))

    search = token_overlap(
        page_a.get("search_text", ""),
        page_b.get("search_text", "")
    )

    excerpt = token_overlap(
        page_a.get("excerpt", ""),
        page_b.get("excerpt", "")
    )

    wa = page_a.get("word_count", 0)
    wb = page_b.get("word_count", 0)

    word_similarity = 0
    if max(wa, wb) > 0:
        word_similarity = 1 - abs(wa - wb) / max(wa, wb)

    semantic_overlap = concept_overlap  # placeholder for future expansion
    
    return {
        "concept_overlap": concept,
        "search_similarity": search,
        "excerpt_similarity": excerpt,
        "word_similarity": word_similarity
    }

# =========================================================
# PAGE GRAPH (CONSUMER LAYER ONLY)
# =========================================================

def build_page_graph(registry):
    """
    Derived navigation layer only.
    Not part of truth layer.
    """

    page_graph = {}

    for url, data in registry.items():

        related_scores = {}

        for other_url, other_page in registry.items():

            if other_url == url:
                continue

            similarity = compare_pages(data, other_page)

            score = (
                similarity["concept_overlap"] * 5
                + similarity["search_similarity"] * 3
                + similarity["excerpt_similarity"] * 2
                + similarity["word_similarity"] * 1
            )

            if score > 0:
                related_scores[other_url] = score

        ranked = sorted(
            related_scores.items(),
            key=lambda x: (-x[1], x[0])
        )

        page_graph[url] = {
            "concepts": data["concepts"],
            "related": [u for u, _ in ranked[:10]]
        }

    return page_graph


# =========================================================
# TRUTH LAYER ASSEMBLY
# =========================================================

def build_semantic_salience(registry):

    nodes, edges = build_graph(registry)

    salience = build_salience(registry, edges)

    page_graph = build_page_graph(registry)

    return {
        "version": "4.2",
        "philosophy": {
            "graph": "structure of reality",
            "salience": "weighting of reality",
            "consumers": "read only"
        },

        # TRUTH LAYER
        "nodes": nodes,
        "edges": edges,
        "salience": salience,

        # DERIVED LAYER (NON-TRUTH)
        "page_graph": page_graph
    }


# =========================================================
# FILE DISCOVERY
# =========================================================

def find_html_files(root):
    html_files = []

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".html"):
                full = os.path.join(dirpath, filename)
                rel = os.path.relpath(full, root)
                html_files.append(rel)

    return sorted(html_files)


# =========================================================
# MAIN
# =========================================================

def main():

    root = os.getcwd()

    html_files = find_html_files(root)

    print("📂 scanning root:", root)
    print("📦 html files discovered:", len(html_files))

    registry = build_registry(root, html_files)

    print("📦 registry entries:", len(registry))

    semantic = build_semantic_salience(registry)

    output_path = os.path.join(root, "assets/semantic-salience.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(semantic, f, indent=2, ensure_ascii=False)

    print("🌌 semantic-salience COMPLETE (v4.2 CANONICAL TRUTH MODEL)")
    print("📁 output:", output_path)
    print("📦 nodes:", len(semantic["nodes"]))
    print("📦 edges:", len(semantic["edges"]))
    print("🧠 salience concepts:", len(semantic["salience"]))
    print("WORD SAMPLE:", url, len(text), text[:200])

if __name__ == "__main__":
    main()
