#!/bin/bash
set -euo pipefail

echo "🧠 Building content model..."
python3 scripts/build-content-model.py
