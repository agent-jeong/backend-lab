#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
QUARTZ_DIR="$ROOT_DIR/.quartz-work/quartz"
export npm_config_cache="$ROOT_DIR/.quartz-work/npm-cache"

bash "$ROOT_DIR/site/scripts/ensure-quartz.sh"
bash "$ROOT_DIR/site/scripts/prepare-content.sh" "$QUARTZ_DIR/content"

cd "$QUARTZ_DIR"

npx quartz plugin install --from-config

if [ -n "${QUARTZ_BASE_DIR:-}" ]; then
  npx quartz build --baseDir "$QUARTZ_BASE_DIR"
else
  npx quartz build
fi
