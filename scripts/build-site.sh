#!/bin/bash
set -euo pipefail

echo "🌌 building semantic-salience..."
python scripts/build-semantic-salience.py

echo "🏠 building homepage intelligence..."
python scripts/build-homepage-intelligence.py

echo "🧩 injecting content into pages..."
python scripts/inject-content.py

echo "✅ build complete"
