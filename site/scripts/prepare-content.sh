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
  "03-work-cases"
  "04-interview-cases"
  "05-ai-workflows"
  "_assets"
)

for path in "${PUBLIC_PATHS[@]}"; do
  if [ -d "$ROOT_DIR/$path" ]; then
    mkdir -p "$CONTENT_DIR/$path"
    if [ "$path" = "00-home" ]; then
      # 작업용 문서는 저장소에만 두고 블로그에는 올리지 않는다
      rsync -a --exclude ".DS_Store" --exclude "index.md" --exclude "daily-study-board.md" --exclude "mastery-map.md" --exclude "learning-principles.md" "$ROOT_DIR/$path/" "$CONTENT_DIR/$path/"
    else
      rsync -a --exclude ".DS_Store" "$ROOT_DIR/$path/" "$CONTENT_DIR/$path/"
    fi
  fi
done

python3 "$ROOT_DIR/site/scripts/inject-dates.py" "$ROOT_DIR" "$CONTENT_DIR"
