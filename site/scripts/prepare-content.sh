#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTENT_DIR="${1:-$ROOT_DIR/.quartz-work/quartz/content}"

rm -rf "$CONTENT_DIR"
mkdir -p "$CONTENT_DIR"

cp "$ROOT_DIR/00-home/index.md" "$CONTENT_DIR/index.md"

PUBLIC_PATHS=(
  "00-home"
  "01-core"
  "02-practical-backend"
  "03-case-studies"
  "04-interview"
  "05-ai-workflows"
  "_assets"
)

for path in "${PUBLIC_PATHS[@]}"; do
  if [ -d "$ROOT_DIR/$path" ]; then
    mkdir -p "$CONTENT_DIR/$path"
    rsync -a --exclude ".DS_Store" "$ROOT_DIR/$path/" "$CONTENT_DIR/$path/"
  fi
done
