#!/usr/bin/env bash
# Build the love.js (WebAssembly) version of StarryKnight into web/.
# Usage: tools/build_web.sh [output_dir]   (default: <repo>/web)
# Needs node + npm + zip. love.js is installed user-locally in .web-tools/.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$REPO/web}"
TOOLS="${WEB_TOOLS_DIR:-$REPO/.web-tools}"
LOVEJS_VERSION="${LOVEJS_VERSION:-11.4.1}"

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
