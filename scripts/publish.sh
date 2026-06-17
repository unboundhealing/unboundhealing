#!/bin/zsh

set -e

PROJECT_ROOT="/Users/unboundhealing/Documents/Unbound Healing/Web Design"

cd "$PROJECT_ROOT" || exit 1

echo "🚀 Publishing pipeline started..."

# =========================
# 1. SYNC FIRST (critical)
# =========================
echo "🔄 Syncing with remote..."
git pull --rebase origin main || exit 1

# =========================
# 2. GENERATE RSS
# =========================
echo "📡 Generating RSS..."
./scripts/generate-rss.sh

# =========================
# 3. STAGE CHANGES
# =========================
git add feed.xml scripts/generate-rss.sh scripts/publish.sh

# =========================
# 4. SAFETY CHECK
# =========================
if git diff --cached --quiet; then
  echo "🟡 No changes to publish"
  exit 0
fi

# =========================
# 5. COMMIT + PUSH
# =========================
git commit -m "publish: update site + rss feed"
git push

echo "✅ Publish complete"
