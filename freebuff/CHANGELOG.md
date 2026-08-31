# Changelog - Freebuff Feature Map Adapter

## v0.12.0 - 2026-08-31

### ✨ Fitur Baru

#### Pre-commit Hook Otomatis
- ✨ Git pre-commit hook yang jalan otomatis sebelum commit
- ✨ Blocks commit jika ada pending drift bisnis
- ✨ Install script untuk memasang hook (`install_git_hook.sh`)
- ✨ Override support: `FEATURE_MAP_ACK=1 git commit ...`

#### Cara Kerja Pre-commit
1. Hook jalan otomatis sebelum `git commit`
2. Cek apakah ada pending drift bisnis (`.freebuff/feature-map-pending/*.json`)
3. Jika ada yang tersentuh staged files → commit diblokir
4. Jika tidak ada atau flow tidak tersentuh → commit dilanjutkan

### 🔧 Perbaikan

#### Parser Bug Fix
- 🐛 Fix: History section salah parse sebagai invariants
- 🐛 Fix: Indent detection lebih akurat

### 📝 Dokumentasi

- ✨ Update README dengan pre-commit hook section
- ✨ Update CHANGELOG dengan v0.12.0
- ✨ Tambah install script documentation

---

## v0.12.0 - 2026-08-31

### ✨ Fitur Baru

#### Freebuff Adapter (`freebuff/freebuff_adapter.py`)
- ✨ Parser FEATURE-MAP.yaml tanpa依赖 PyYAML
- ✨ Hook check untuk file yang diedit
- ✨ Audit flow command
- ✨ Status check command
- ✨ Reminder otomatis saat edit touchpoint

#### Hooks System
- ✨ Menggunakan `run_file_change_hooks` Freebuff
- ✨ Format reminder yang jelas dan informatif
- ✨ Support untuk semua jenis file (Python, JS, TS, Java, Kotlin, Dart, Vue)

#### Commands
- ✨ `audit [flow]` - Audit flow tertentu atau semua flow
- ✨ `status` - Tampilkan status sync
- ✨ `hook <file>` - Cek apakah file adalah touchpoint

### 📝 Dokumentasi

- ✨ `README.md` - Dokumentasi utama
- ✨ `COMMANDS_FREEBUFF.md` - Command reference
- ✨ `CHANGELOG.md` - Changelog

### 🧪 Testing

- ✨ Parser YAML subset testing
- ✨ Touchpoint matching testing
- ✨ Reminder generation testing

### 🔧 Konfigurasi

- ✨ `.freebuff/hooks.json` - Hook configuration untuk Freebuff
- ✨ `FEATURE-MAP.yaml` - Sample registry

---

## v0.11.1 - Original (Claude Code/Codex)

### Rilis Asli
- Plugin untuk Claude Code dan Codex
- Native hooks dan commands
- Marketplace installation

---

## Roadmap

### v1.2.0 (Planned)
- [ ] Flow sync apply adapter
- [ ] Blueprint import support
- [ ] Multi-repo flow support

### v1.3.0 (Planned)
- [ ] GUI untuk management flow
- [ ] Integration dengan Git hooks
- [ ] Auto-detect touchpoints dari code
- [ ] Report generation

---

## Cara Update

```bash
# Pull latest changes
git pull

# Run setup
bash freebuff/setup.sh

# Install/reinstall git hook
bash freebuff/install_git_hook.sh

# Verify
python3 freebuff/freebuff_adapter.py status
```

## Troubleshooting Update

Jika ada masalah setelah update:

```bash
# Clean cache
rm -rf .freebuff/__pycache__

# Re-run setup
bash freebuff/setup.sh

# Reinstall git hook
bash freebuff/install_git_hook.sh

# Test adapter
python3 freebuff/freebuff_adapter.py audit
```
