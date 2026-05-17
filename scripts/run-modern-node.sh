#!/bin/sh
set -eu

node_major() {
  "$1" -e "process.stdout.write(String(process.versions.node.split('.')[0]))" 2>/dev/null || true
}

use_if_modern() {
  candidate="$1"
  shift
  if [ -x "$candidate" ]; then
    major="$(node_major "$candidate")"
    if [ "${major:-0}" -ge 20 ] 2>/dev/null; then
      exec "$candidate" "$@"
    fi
  fi
}

if command -v node >/dev/null 2>&1; then
  use_if_modern "$(command -v node)" "$@"
fi

use_if_modern "/Applications/Codex.app/Contents/Resources/node" "$@"
use_if_modern "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" "$@"

echo "Node.js 20 or newer is required to run this script." >&2
echo "Install a current Node.js LTS release, then retry." >&2
exit 1
