#!/bin/bash
# Install git pre-commit hook untuk feature-map
# Menjalankan script ini akan memasang hook otomatis

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔧 Installing feature-map pre-commit hook..."
echo ""

# Check if git repo
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ Bukan git repository!"
    exit 1
fi

# Create hooks directory if not exists
mkdir -p "$PROJECT_ROOT/.git/hooks"

# Create pre-commit hook
HOOK_FILE="$PROJECT_ROOT/.git/hooks/pre-commit"

if [ -f "$HOOK_FILE" ]; then
    echo "⚠️  Pre-commit hook sudah ada"
    echo "   Mengecek apakah sudah ada feature-map hook..."
    
    if grep -q "feature-map" "$HOOK_FILE"; then
        echo "   ✅ Feature-map hook sudah terinstall"
        exit 0
    fi
    
    echo "   Menambahkan feature-map hook ke existing hook..."
    echo "" >> "$HOOK_FILE"
    echo "# Feature Map pre-commit hook" >> "$HOOK_FILE"
    echo "python3 \"$SCRIPT_DIR/freebuff_adapter.py\" pre-commit" >> "$HOOK_FILE"
else
    echo "📝 Membuat pre-commit hook baru..."
    cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash
# Pre-commit hook untuk feature-map
# Dijalankan otomatis oleh git sebelum commit

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
EOF
fi

# Make hook executable
chmod +x "$HOOK_FILE"

echo ""
echo "✅ Pre-commit hook berhasil diinstall!"
echo ""
echo "Cara kerja:"
echo "  - Hook akan jalan otomatis sebelum git commit"
echo "  - Jika ada drift bisnis, commit akan diblokir"
echo "  - Override: FEATURE_MAP_ACK=1 git commit ..."
echo ""
echo "Test dengan:"
echo "  python3 freebuff/freebuff_adapter.py pre-commit"
