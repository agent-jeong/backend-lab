#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="$ROOT_DIR/.quartz-work"
QUARTZ_DIR="$WORK_DIR/quartz"
export npm_config_cache="$WORK_DIR/npm-cache"

mkdir -p "$WORK_DIR"

if [ ! -d "$QUARTZ_DIR/.git" ]; then
  git clone --branch v5 --depth 1 https://github.com/jackyzha0/quartz.git "$QUARTZ_DIR"
fi

cd "$QUARTZ_DIR"

if [ ! -d "node_modules" ]; then
  npm ci
fi

cp "$ROOT_DIR/site/quartz.config.yaml" "$QUARTZ_DIR/quartz.config.yaml"

if [ -f "$ROOT_DIR/site/quartz.template" ]; then
  cp "$ROOT_DIR/site/quartz.template" "$QUARTZ_DIR/quartz.ts"
fi

if [ -f "$ROOT_DIR/site/styles/custom.scss" ]; then
  cp "$ROOT_DIR/site/styles/custom.scss" "$QUARTZ_DIR/quartz/styles/custom.scss"
fi
