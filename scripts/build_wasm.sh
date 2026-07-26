#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$ROOT_DIR/web/dist"
mkdir -p "$OUTPUT_DIR"

if ! command -v em++ >/dev/null 2>&1; then
  echo "error: em++ was not found. Activate emsdk before running this script." >&2
  exit 1
fi

em++ \
  "$ROOT_DIR/wasm/search_engine.cpp" \
  "$ROOT_DIR/wasm/bindings.cpp" \
  -I"$ROOT_DIR/wasm" \
  -std=c++17 \
  -O3 \
  -flto \
  -lembind \
  -sMODULARIZE=1 \
  -sEXPORT_NAME=createSearchEngine \
  -sALLOW_MEMORY_GROWTH=1 \
  -sENVIRONMENT=web \
  -sFILESYSTEM=0 \
  -sASSERTIONS=0 \
  -o "$OUTPUT_DIR/search_engine.js"

echo "Generated:"
ls -lh "$OUTPUT_DIR/search_engine.js" "$OUTPUT_DIR/search_engine.wasm"
