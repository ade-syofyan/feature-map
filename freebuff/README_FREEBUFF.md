# Feature Map - Freebuff Adapter

## Status Kompatibilitas

| Fitur | Status | Keterangan |
|-------|--------|------------|
| SKILL.md (behavioral guidelines) | ✅ Bisa dipakai | Ikuti guideline saat edit file |
| Hooks (PostToolUse reminders) | ✅ Adapter dibuat | Menggunakan run_file_change_hooks |
| Commands (flow-audit, dll) | ✅ Adapter dibuat | Menggunakan run_terminal_command |
| FEATURE-MAP.yaml workflow | ✅ Bisa dipakai | Manual + reminder dari SKILL.md |
| Pre-commit hook | ✅ Otomatis | Blocks commit jika ada drift |

## File Structure

```
freebuff/
├── freebuff_adapter.py    # Adapter utama (Python) — semua command
├── run_hook.sh           # Shell wrapper untuk hook
├── precommit_hook.sh     # Pre-commit hook wrapper
├── install_git_hook.sh   # Install git pre-commit hook
├── setup.sh             # Setup script
├── README.md            # Dokumentasi utama
├── README_FREEBUFF.md   # Dokumentasi ini
├── COMMANDS_FREEBUFF.md # Command reference
└── CHANGELOG.md         # Changelog

skills/feature-map/
├── SKILL.md             # Behavioral guidelines (original)
└── SKILL_FREEBUFF.md    # Behavioral guidelines (Freebuff)
```

**Note:** Script `hooks/flow_audit_freebuff.sh`, `hooks/flow_sync_apply_freebuff.sh`,
`hooks/flow_map_init_freebuff.sh`, dan `hooks/precommit_check_freebuff.sh` **tidak ada**.
Semua command dijalankan langsung via `freebuff/freebuff_adapter.py`.

## Cara Penggunaan di Freebuff

### 1. Audit Flow
```bash
python3 freebuff/freebuff_adapter.py audit
python3 freebuff/freebuff_adapter.py audit partner-registration
```

### 2. Cek Status
```bash
python3 freebuff/freebuff_adapter.py status
```

### 3. Cek File (PostToolUse)
```bash
python3 freebuff/freebuff_adapter.py hook src/api/partner.py
```

### 4. Init Feature Map
```bash
python3 freebuff/freebuff_adapter.py init
```

### 5. Sync Apply (MVP — manual only)
```bash
python3 freebuff/freebuff_adapter.py sync-apply
# → List pending drift, user apply manual, lalu hapus file pending
```

### 6. Pre-commit Check
```bash
python3 freebuff/freebuff_adapter.py pre-commit
```

## Troubleshooting

### Hook tidak jalan
```bash
python3 freebuff/freebuff_adapter.py hook src/test.py
```

### Command tidak dikenali
```bash
python3 freebuff/freebuff_adapter.py <command> [args]
```

### FEATURE-MAP.yaml tidak terbaca
Pastikan file ada di root project dan formatnya benar.
