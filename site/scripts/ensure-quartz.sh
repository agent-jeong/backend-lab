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

GISCUS_REPO="${GISCUS_REPO:-agent-jeong/backend-lab}"
GISCUS_REPO_ID="${GISCUS_REPO_ID:-R_kgDOSn8Rqg}"
GISCUS_CATEGORY="${GISCUS_CATEGORY:-Announcements}"
GISCUS_CATEGORY_ID="${GISCUS_CATEGORY_ID:-DIC_kwDOSn8Rqs4C-UvH}"
GISCUS_LANG="${GISCUS_LANG:-ko}"

if [ "${ENABLE_GISCUS_COMMENTS:-true}" = "true" ]; then
  TMP_CONFIG="$(mktemp)"

  sed '/^layout:$/q' "$QUARTZ_DIR/quartz.config.yaml" | sed '$d' > "$TMP_CONFIG"
  cat >> "$TMP_CONFIG" <<YAML
  - source: github:quartz-community/comments
    enabled: true
    options:
      provider: giscus
      options:
        repo: ${GISCUS_REPO}
        repoId: ${GISCUS_REPO_ID}
        category: ${GISCUS_CATEGORY}
        categoryId: ${GISCUS_CATEGORY_ID}
        lang: ${GISCUS_LANG}
        mapping: pathname
        strict: true
        reactionsEnabled: true
        inputPosition: bottom
    layout:
      position: afterBody
      priority: 10
YAML
  sed -n '/^layout:$/,$p' "$QUARTZ_DIR/quartz.config.yaml" >> "$TMP_CONFIG"
  mv "$TMP_CONFIG" "$QUARTZ_DIR/quartz.config.yaml"
fi

if [ -f "$ROOT_DIR/site/quartz.template" ]; then
  cp "$ROOT_DIR/site/quartz.template" "$QUARTZ_DIR/quartz.ts"
fi

if [ -f "$ROOT_DIR/site/styles/custom.scss" ]; then
  cp "$ROOT_DIR/site/styles/custom.scss" "$QUARTZ_DIR/quartz/styles/custom.scss"
fi
