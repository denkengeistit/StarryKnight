#!/usr/bin/env bash
# Pull main and rebuild web/ only when HEAD changed. Run by starryknight-web.timer.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
before="$(git rev-parse HEAD)"
git pull --ff-only origin main
after="$(git rev-parse HEAD)"
if [ "$before" != "$after" ] || [ ! -f web/index.html ]; then
  tools/build_web.sh
else
  echo "no change ($after)"
fi
