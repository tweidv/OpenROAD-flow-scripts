#!/usr/bin/env bash
# Local ORFS build (no Docker, no Bazel). Requires sudo for system dependencies.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ $EUID -ne 0 ]]; then
  echo "Run dependency setup with sudo:"
  echo "  sudo $0"
  exit 1
fi

echo "==> Installing ORFS / OpenROAD system dependencies (Debian/Ubuntu)..."
./setup.sh

echo "==> Building OpenROAD, Yosys, and kepler-formal locally..."
./build_openroad.sh --local

echo "==> Build finished. Verify with:"
echo "  source ./env.sh"
echo "  yosys -help"
echo "  openroad -help"
echo "  cd flow && make"
