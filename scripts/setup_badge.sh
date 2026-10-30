#!/usr/bin/env bash
# SAINTCON 2026 Badge Setup Wrapper
# Runs scripts/setup_badge.py with python3
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/setup_badge.py" "$@"
