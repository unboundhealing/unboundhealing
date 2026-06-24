# plugin-registry.py (canonical plugin truth router v2)

"""
Single responsibility:
- Declare plugin surface
- Provide deterministic execution order
- Maintain alignment with semantic-salience consumer architecture

IMPORTANT:
- No logic here
- No rendering here
- No salience interpretation here
"""

from enhance_pages import (
    plugin_related_content,
    plugin_tracking,
    plugin_future_magic,
    load_homepage_intelligence,
)

# =========================================================
# SINGLE SOURCE OF TRUTH (PLUGIN SURFACE ONLY)
# =========================================================

PLUGIN_REGISTRY = {
    # -------------------------------------------------
    # CORE INFRASTRUCTURE
    # -------------------------------------------------
    "tracking": plugin_tracking,

    # -------------------------------------------------
    # HOMEPAGE INTELLIGENCE (NEW PRIMARY LAYER)
    # derived from homepage-intelligence.json
    # -------------------------------------------------
    "homepage_intelligence": load_homepage_intelligence,

    # -------------------------------------------------
    # SEMANTIC NAVIGATION LAYER
    # -------------------------------------------------
    "related_content": plugin_related_content,

    # -------------------------------------------------
    # EXPERIMENTAL / FUTURE EXTENSIONS
    # -------------------------------------------------
    "future_magic": plugin_future_magic,
}

# =========================================================
# DETERMINISTIC EXECUTION ORDER (CONSUMER SAFE)
# =========================================================

PLUGIN_ORDER = [
    "tracking",
    "homepage_intelligence",
    "related_content",
    "future_magic",
]


# =========================================================
# OPTIONAL EXPORT HELPERS (SAFE CONSUMER API)
# =========================================================

def get_plugin(name):
    """Safe lookup for enhance_pages.py"""
    return PLUGIN_REGISTRY.get(name)


def get_ordered_plugins():
    """Returns plugins in deterministic execution order"""
    return [
        (name, PLUGIN_REGISTRY[name])
        for name in PLUGIN_ORDER
        if name in PLUGIN_REGISTRY
    ]
