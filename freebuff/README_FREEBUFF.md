# Feature Map - Freebuff Adapter

## Status Kompatibilitas

| Fitur | Status | Keterangan |
|-------|--------|------------|
| SKILL.md (behavioral guidelines) | ✅ Bisa dipakai | Ikuti guideline saat edit file |
| Hooks (PostToolUse reminders) | ✅ Adapter dibuat | Menggunakan run_file_change_hooks |
| Commands (flow-audit, dll) | ✅ Adapter dibuat | Menggunakan run_terminal_command |
| FEATURE-MAP.yaml workflow | ✅ Bisa dipakai | Manual + reminder dari SKILL.md |

## Cara Penggunaan di Freebuff

### 1. Audit Flow
Ketik di chat:
```
Jalankan feature-map flow audit untuk flow partner-registration
```
Agent akan menjalankan script `hooks/flow_audit_freebuff.sh`

### 2. Sync Invariants
Ketik di chat:
```
Jalankan feature-map flow sync apply
```
Agent akan menjalankan script `hooks/flow_sync_apply_freebuff.sh`

### 3. Init Feature Map
Ketik di chat:
```
Jalankan feature-map init untuk project ini
```
Agent akan menjalankan script `hooks/flow_map_init_freebuff.sh`

### 4. Reminder Otomatis
Setelah edit file, agent akan:
1. Mengecek apakah file yang diedit adalah touchpoint
2. Jika ya, mengingatkan untuk cek touchpoint lain
3. Menyarankan update FEATURE-MAP.yaml jika ada perubahan bisnis

### 5. Pre-commit Check
Sebelum commit, jalankan:
```
Jalankan feature-map pre-commit check
```
Agent akan menjalankan script `hooks/precommit_check_freebuff.sh`

## File Structure

```
freebuff/
├── README_FREEBUFF.md          # Dokumentasi ini
├── hooks/
│   ├── feature_map_hook.py     # Hook utama (PostToolUse)
│   ├── feature_map_session_start.py  # SessionStart hook
│   ├── feature_map_stop.py     # Stop hook
│   ├── precommit_check.py      # Pre-commit check
│   └── *.sh                    # Freebuff adapter scripts
├── skills/
│   └── feature-map/
│       └── SKILL.md            # Behavioral guidelines
└── commands/
    └── *.md                    # Command documentation
```

## Troubleshooting

### Hook tidak jalan
- Pastikan Python3 terinstall
- Jalankan manual: `python3 hooks/feature_map_hook.py`

### Command tidak dikenali
- Gunakan format: `Jalankan feature-map <command>`
- Atau: `Run feature-map <command>`

### Reminder tidak muncul
- Pastikan file yang diedit ada di touchpoints
- Cek FEATURE-MAP.yaml sudah benar
