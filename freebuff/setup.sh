#!/bin/bash
# Feature Map - Freebuff Setup Script
# Menyiapkan adapter untuk menjalankan feature-map di Freebuff

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔧 Feature Map - Freebuff Setup"
echo "================================"
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3 terinstall"
else
    echo "❌ Python3 tidak ditemukan"
    exit 1
fi

# Create .freebuff directory if not exists
mkdir -p "$PROJECT_ROOT/.freebuff"
echo "✅ Direktori .freebuff siap"

# Create symlink for easy access
if [ ! -L "$PROJECT_ROOT/.freebuff/feature-map" ]; then
    ln -sf "$SCRIPT_DIR/freebuff_adapter.py" "$PROJECT_ROOT/.freebuff/feature-map"
    echo "✅ Symlink feature-map dibuat"
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR/freebuff_adapter.py"
chmod +x "$SCRIPT_DIR/../hooks/freebuff_feature_map_hook.py" 2>/dev/null || true

echo ""
echo "================================"
echo "✅ Setup selesai!"
echo ""
echo "Cara penggunaan:"
echo "  python3 $SCRIPT_DIR/freebuff_adapter.py hook <file>"
echo "  python3 $SCRIPT_DIR/freebuff_adapter.py audit [flow]"
echo "  python3 $SCRIPT_DIR/freebuff_adapter.py status"
echo ""
echo "Atau gunakan:"
echo "  python3 $PROJECT_ROOT/.freebuff/feature-map hook <file>"
