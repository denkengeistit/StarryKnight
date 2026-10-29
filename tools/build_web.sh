#!/usr/bin/env bash
# Build the love.js (WebAssembly) version of StarryKnight into web/.
# Usage: tools/build_web.sh [output_dir]   (default: <repo>/web)
# Needs node + npm + zip. love.js is installed user-locally in .web-tools/.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$REPO/web}"
TOOLS="${WEB_TOOLS_DIR:-$REPO/.web-tools}"
LOVEJS_VERSION="${LOVEJS_VERSION:-11.4.1}"

# love.js runs PUC Lua 5.1: no goto/labels, no integer division, etc.
# Refuse to build if any .lua file fails a Lua 5.1 parse (needs luac5.1).
if command -v luac5.1 >/dev/null 2>&1; then
  ( cd "$REPO" && git ls-files '*.lua' | while read -r f; do luac5.1 -p "$f" || exit 1; done ) \
    || { echo "build_web: Lua 5.1 syntax check failed; not building" >&2; exit 1; }
else
  echo "build_web: luac5.1 not found, skipping Lua 5.1 syntax check" >&2
fi

if [ ! -x "$TOOLS/node_modules/.bin/love.js" ]; then
  mkdir -p "$TOOLS"
  npm install --prefix "$TOOLS" --no-audit --no-fund "love.js@$LOVEJS_VERSION"
fi

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# Game files only (not love.app, docs, archive, tools, git data).
( cd "$REPO" && zip -qr "$STAGE/game.love" conf.lua main.lua src assets )

# -c: compatibility build, single-threaded, needs no COOP/COEP headers.
# -m: memory in bytes.
BUILD="$STAGE/out"
"$TOOLS/node_modules/.bin/love.js" -c -m 67108864 -t "StarryKnight" "$STAGE/game.love" "$BUILD"
test -f "$BUILD/index.html"

# Swap in atomically-ish so a failed build never leaves web/ empty.
rm -rf "$OUT.new"
mv "$BUILD" "$OUT.new"
rm -rf "$OUT"
mv "$OUT.new" "$OUT"
echo "built: $OUT/index.html"
