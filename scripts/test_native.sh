#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/native-test"
mkdir -p "$BUILD_DIR"

g++ \
  "$ROOT_DIR/wasm/search_engine.cpp" \
  "$ROOT_DIR/wasm/native_smoke_test.cpp" \
  -I"$ROOT_DIR/wasm" \
  -std=c++17 \
  -O2 \
  -Wall \
  -Wextra \
  -Wpedantic \
  -o "$BUILD_DIR/search_engine_smoke_test"

"$BUILD_DIR/search_engine_smoke_test"
