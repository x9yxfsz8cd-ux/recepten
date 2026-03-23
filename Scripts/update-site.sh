#!/bin/bash
# update-site.sh — Kopieer recepten.json van iCloud naar de website en push naar GitHub

ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs/recepten/recepten.json"
REPO="$HOME/Documents/recepten/docs/data/recepten.json"

if [ ! -f "$ICLOUD" ]; then
  echo "❌ recepten.json niet gevonden in iCloud Drive"
  exit 1
fi

cp "$ICLOUD" "$REPO"
echo "✅ recepten.json gekopieerd"

cd "$HOME/Documents/recepten"
git add docs/data/recepten.json
git commit -m "Recepten bijgewerkt $(date '+%Y-%m-%d')"
git push

echo "🚀 Website bijgewerkt! Wacht ±1 minuut voor GitHub Pages."
