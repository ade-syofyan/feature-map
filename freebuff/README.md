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
| sync-apply | ⚠️ MVP | List pending saja, apply manual |

## 🚀 Quick Start

### 1. Setup
```bash
bash freebuff/setup.sh
```

### 2. Install Git Pre-commit Hook
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
```
Jalankan feature-map audit untuk flow partner-registration
```

#### Cek Status
```
Cek status feature-map
```

#### Cek File (PostToolUse)
```
python3 freebuff/freebuff_adapter.py hook src/api/partner.py
```

#### Init Feature Map
```
Buat FEATURE-MAP.yaml baru untuk project ini
```

#### Sync Apply (MVP)
```
Jalankan feature-map sync-apply
```
**Catatan:** `sync-apply` saat ini hanya menampilkan daftar pending drift beserta
instruksi manual. Belum melakukan apply/clear otomatis. User perlu:
1. Baca file pending
2. Update FEATURE-MAP.yaml secara manual
3. Hapus file pending: `rm .freebuff/feature-map-pending/<flow>.json`

#### Pre-commit Check (Otomatis!)
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
├── install_git_hook.sh   # Script install git hook
├── setup.sh             # Setup script
├── README.md            # Dokumentasi ini
├── COMMANDS_FREEBUFF.md # Command reference
└── CHANGELOG.md         # Changelog
```

## 🔧 Command Reference

| Command | Deskripsi | Exit Code |
|---------|-----------|-----------|
| `audit [flow]` | Audit flow | 0=ok, 1=error/not found |
| `status` | Cek status | 0 |
| `hook <file>` | Cek file | 0 (touchpoint atau bukan) |
| `sync-apply` | List pending drift (manual apply) | 0=no pending, 1=pending ada |
| `init` | Buat FEATURE-MAP.yaml | 0=ok, 1=gagal |
| `pre-commit` | Pre-commit check | 0=allow, 1=block |

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
FEATURE_MAP_ACK=1 git commit -m "message"
git commit --no-verify -m "message"
```

## 📊 Changelog

Lihat [CHANGELOG.md](CHANGELOG.md) untuk detail perubahan.

### v0.12.0 (2026-08-31)
- ✨ Freebuff adapter (hook, audit, status, sync-apply, init, pre-commit)
- ✨ Repo-style glob matching (`**` support)
- ✨ YAML inline comment parser
- ✅ Proper exit codes (0/1/2)
- 🐛 Fix parser bug (history section)
- 📝 Dokumentasi lengkap

## 🐛 Troubleshooting

### Pre-commit hook tidak jalan
```bash
ls -la .git/hooks/pre-commit
bash freebuff/install_git_hook.sh
```

### Commit diblokir
```bash
FEATURE_MAP_ACK=1 git commit -m "refactor"
```

### FEATURE-MAP.yaml tidak terbaca
Pastikan file ada di root project dan formatnya benar.

## 📚 Link Penting

- [Feature Map Original](https://github.com/ade-syofyan/feature-map)
- [Claude Code Plugin](https://github.com/ade-syofyan/feature-map#claude-code-usage)
- [Codex Skill](https://github.com/ade-syofyan/feature-map#codex-usage)

## 📄 Lisensi

MIT License - Sama dengan feature-map original
