# Changelog - Freebuff Feature Map Adapter

## v0.12.1 - 2026-08-31

### Fixes

- Fix exit codes for no-arg usage, unknown command, missing hook argument, and missing flow audit.
- Fix repo-style glob matching: `*` no longer crosses directories, and `**` matches root-level and nested paths.
- Fix YAML inline-comment parsing while preserving `#` inside quoted values.
- Update Freebuff docs to reference the real Python adapter instead of missing shell scripts.
- Expand `FEATURE-MAP.yaml` touchpoints for Freebuff docs, shell wrappers, hook config, and Freebuff skill notes.

---

## v0.12.0 - 2026-08-31

### ✨ Fitur Baru

#### Freebuff Adapter (`freebuff/freebuff_adapter.py`)
- ✨ Parser FEATURE-MAP.yaml tanpa依赖 PyYAML
- ✨ Hook check untuk file yang diedit
- ✨ Audit flow command
- ✨ Status check command
- ✨ Reminder otomatis saat edit touchpoint

#### Pre-commit Hook Otomatis
- ✨ Git pre-commit hook yang jalan otomatis sebelum commit
- ✨ Blocks commit jika ada pending drift bisnis
- ✨ Install script untuk memasang hook (`install_git_hook.sh`)
- ✨ Override support: `FEATURE_MAP_ACK=1 git commit ...`

#### Hooks System
- ✨ Menggunakan `run_file_change_hooks` Freebuff
- ✨ Format reminder yang jelas dan informatif
- ✨ Support untuk semua jenis file (Python, JS, TS, Java, Kotlin, Dart, Vue)

#### Commands
- ✨ `audit [flow]` - Audit flow tertentu atau semua flow
- ✨ `status` - Tampilkan status sync
- ✨ `hook <file>` - Cek apakah file adalah touchpoint
- ✨ `sync-apply` - Lihat pending drift dan instruksi sync
- ✨ `init` - Buat FEATURE-MAP.yaml jika belum ada

### 🔧 Perbaikan

#### Parser Bug Fix
- 🐛 Fix: History section salah parse sebagai invariants
- 🐛 Fix: Indent detection lebih akurat

### 📝 Dokumentasi

- ✨ `README.md` - Dokumentasi utama
- ✨ `COMMANDS_FREEBUFF.md` - Command reference
- ✨ `CHANGELOG.md` - Changelog ini
- ✨ Tambah install script documentation

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

### v0.13.0 (Planned)
- [ ] Flow sync apply adapter (full, bukan hanya list pending)
- [ ] Blueprint import support
- [ ] Multi-repo flow support

### v0.14.0 (Planned)
- [ ] GUI untuk management flow
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
