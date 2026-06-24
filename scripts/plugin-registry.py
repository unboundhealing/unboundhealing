# plugin-registry.py (canonical plugin truth layer)

from enhance_pages import (
    plugin_related_content,
    plugin_tracking,
    plugin_future_magic,
)

# -------------------------------------------------
# SINGLE SOURCE OF TRUTH (plugins only)
# -------------------------------------------------

PLUGIN_REGISTRY = {
    "related_content": plugin_related_content,
    "tracking": plugin_tracking,
    "future_magic": plugin_future_magic,
}

# Optional explicit ordering (consumer-safe determinism)
PLUGIN_ORDER = [
    "related_content",
    "tracking",
    "future_magic",
]
