#!/bin/bash
# Git pre-commit hook untuk feature-map
# Dipanggil otomatis oleh git sebelum commit

# Cari root project
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Cek apakah FEATURE-MAP.yaml ada
if [ ! -f "$PROJECT_ROOT/FEATURE-MAP.yaml" ]; then
    exit 0
fi

# Jalankan pre-commit check
python3 "$PROJECT_ROOT/freebuff/freebuff_adapter.py" pre-commit
EXIT_CODE=$?

# Jika ada blocking, exit dengan kode yang sama
exit $EXIT_CODE
