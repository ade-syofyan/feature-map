#!/bin/bash
# Feature Map - Freebuff Hook Runner
# Dipanggil oleh Freebuff saat file berubah

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FILE="${1:-}"

if [ -z "$FILE" ]; then
    echo "Usage: $0 <file_path>"
    exit 1
fi

# Run adapter hook
python3 "$SCRIPT_DIR/freebuff_adapter.py" hook "$FILE"
