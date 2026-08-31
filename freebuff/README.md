# Feature Map - Freebuff Adapter

> Plugin feature-map yang sudah diadaptasi untuk Freebuff

## 📋 Status Kompatibilitas

| Fitur | Status | Keterangan |
|-------|--------|------------|
| SKILL.md (behavioral guidelines) | ✅ Bisa dipakai | Ikuti guideline saat edit file |
| Hooks (PostToolUse reminders) | ✅ Adapter dibuat | Menggunakan run_file_change_hooks |
| Commands (flow-audit, dll) | ✅ Adapter dibuat | Menggunakan run_terminal_command |
| FEATURE-MAP.yaml workflow | ✅ Bisa dipakai | Manual + reminder dari SKILL.md |
| Pre-commit hook | ✅ Otomatis | Blocks commit jika ada drift |

## 🚀 Quick Start

### 1. Setup
```bash
bash freebuff/setup.sh
```

### 2. Install Git Pre-commit Hook (Baru!)
```bash
bash freebuff/install_git_hook.sh
```

### 3. Audit Flow
```bash
python3 freebuff/freebuff_adapter.py audit
```

### 4. Cek Status
```bash
python3 freebuff/freebuff_adapter.py status
```

## 📖 Dokumentasi

### Cara Penggunaan di Freebuff

#### Audit Flow
Ketik di chat:
```
Jalankan feature-map audit untuk flow partner-registration
```

#### Cek Status
Ketik di chat:
```
Cek status feature-map
```

#### Cek File (PostToolUse)
Setelah edit file, agent akan otomatis mengecek:
```
python3 freebuff/freebuff_adapter.py hook src/api/partner.py
```

#### Init Feature Map
Ketik di chat:
```
Buat FEATURE-MAP.yaml baru untuk project ini
```

#### Pre-commit Check (Otomatis!)
Pre-commit hook akan jalan otomatis sebelum git commit:
```bash
# Jika ada drift, commit akan diblokir
git commit -m "update feature"

# Override jika memang bukan perubahan bisnis
FEATURE_MAP_ACK=1 git commit -m "refactor code"
```

## 📁 Struktur File

```
freebuff/
├── freebuff_adapter.py    # Adapter utama (Python)
├── run_hook.sh           # Shell script untuk hook
├── precommit_hook.sh     # Pre-commit hook wrapper
├── install_git_hook.sh   # Script install git hook (Baru!)
├── setup.sh             # Setup script
├── README.md            # Dokumentasi ini
├── COMMANDS_FREEBUFF.md # Command reference
└── CHANGELOG.md        # Changelog
```

## 🔧 Command Reference

| Command | Deskripsi | Contoh |
|---------|-----------|--------|
| `audit [flow]` | Audit flow | `python3 freebuff/freebuff_adapter.py audit partner-registration` |
| `status` | Cek status | `python3 freebuff/freebuff_adapter.py status` |
| `hook <file>` | Cek file | `python3 freebuff/freebuff_adapter.py hook src/api/partner.py` |
| `pre-commit` | Pre-commit check | `python3 freebuff/freebuff_adapter.py pre-commit` |

## 🔒 Pre-commit Hook

### Cara Kerja
1. Hook jalan otomatis sebelum `git commit`
2. Cek apakah ada pending drift bisnis
3. Jika ya → commit diblokir
4. Jika tidak → commit dilanjutkan

### Install Hook
```bash
bash freebuff/install_git_hook.sh
```

### Override Hook
```bash
# Skip feature-map check
FEATURE_MAP_ACK=1 git commit -m "message"

# Atau gunakan --no-verify
git commit --no-verify -m "message"
```

### Troubleshooting
```bash
# Test hook manual
python3 freebuff/freebuff_adapter.py pre-commit

# Cek apakah hook terinstall
ls -la .git/hooks/pre-commit
```

## 📊 Changelog

Lihat [CHANGELOG.md](CHANGELOG.md) untuk detail perubahan.

### v0.12.0 (2026-08-31)
- ✨ Pre-commit hook otomatis
- ✨ Install script untuk git hook
- 🐛 Fix parser bug (history section)

### v0.12.0 (2026-08-31)
- ✨ Freebuff adapter dibuat
- ✨ Hooks system via run_file_change_hooks
- ✨ Commands via terminal
- 📝 Dokumentasi lengkap

## 🐛 Troubleshooting

### Pre-commit hook tidak jalan
```bash
# Cek apakah hook executable
ls -la .git/hooks/pre-commit

# Install ulang
bash freebuff/install_git_hook.sh
```

### Commit diblokir padahal bukan perubahan bisnis
```bash
# Override check
FEATURE_MAP_ACK=1 git commit -m "refactor"

# Atau skip hook
git commit --no-verify -m "refactor"
```

### FEATURE-MAP.yaml tidak terbaca
Pastikan file ada di root project dan formatnya benar.

## 📚 Link Penting

- [Feature Map Original](https://github.com/ade-syofyan/feature-map)
- [Claude Code Plugin](https://github.com/ade-syofyan/feature-map#claude-code-usage)
- [Codex Skill](https://github.com/ade-syofyan/feature-map#codex-usage)

## 🤝 Kontribusi

Untuk kontribusi ke Freebuff adapter:
1. Fork repository
2. Buat branch feature
3. Commit perubahan
4. Push ke branch
5. Buat Pull Request

## 📄 Lisensi

MIT License - Sama dengan feature-map original
