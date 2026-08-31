# Feature Map Commands - Freebuff Reference

## 📋 Ringkasan Perintah

```bash
python3 freebuff/freebuff_adapter.py <command> [args]
```

## 🔧 Command Detail

### `audit [flow]`
Audit flow tertentu atau semua flow.
```bash
python3 freebuff/freebuff_adapter.py audit
python3 freebuff/freebuff_adapter.py audit partner-registration
```
**Exit:** 0 = ok, 1 = flow tidak ditemukan

### `status`
Tampilkan status sync semua flow.
```bash
python3 freebuff/freebuff_adapter.py status
```
**Exit:** 0

### `hook <file>`
Cek apakah file adalah touchpoint.
```bash
python3 freebuff/freebuff_adapter.py hook src/api/partner.py
```
**Exit:** 0 (selalu, output kosong jika bukan touchpoint)

### `sync-apply` ⚠️ MVP
List pending drift dan instruksi sync **manual**.

**⚠️ MVP Behavior — belum apply/clear otomatis.**
```bash
python3 freebuff/freebuff_adapter.py sync-apply
```
Output menampilkan:
- Daftar flow yang punya pending drift
- Instruksi manual:
  1. Baca file pending
  2. Update FEATURE-MAP.yaml
  3. Hapus file pending: `rm .freebuff/feature-map-pending/<flow>.json`

**Exit:** 0 = tidak ada pending, 1 = ada pending

### `init`
Buat FEATURE-MAP.yaml minimal jika belum ada.
```bash
python3 freebuff/freebuff_adapter.py init
```
**Exit:** 0 = ok/sudah ada, 1 = gagal buat file

### `pre-commit`
Pre-commit check — blocks commit jika ada pending drift.
```bash
python3 freebuff/freebuff_adapter.py pre-commit
```
**Exit:** 0 = allow commit, 1 = block commit

### `hook <file>` tanpa argumen
**Exit:** 2 (error, menampilkan usage)

### Unknown command
```bash
python3 freebuff/freebuff_adapter.py does-not-exist
```
**Exit:** 2 (error, menampilkan pesan error)

### No command (usage)
```bash
python3 freebuff/freebuff_adapter.py
```
**Exit:** 2 (menampilkan daftar command)

## 📊 Workflow Freebuff

1. **Saat edit file**: Agent akan mengecek apakah file adalah touchpoint
2. **Jika ya**: Agent akan mengingatkan untuk cek touchpoint lain
3. **Jika ada perubahan bisnis**: Agent akan menyarankan update FEATURE-MAP.yaml
4. **Sebelum selesai task**: Agent akan memastikan semua invariant konsisten

## 📈 Perbedaan dengan Claude Code

| Fitur | Claude Code | Freebuff |
|-------|-------------|----------|
| Hook otomatis | ✅ PostToolUse | ⚠️ Manual via agent |
| Slash commands | ✅ /feature-map:xxx | ❌ Tidak ada |
| Reminder | ✅ Otomatis | ✅ Via SKILL.md |
| Pre-commit | ✅ Otomatis | ✅ Otomatis |
| sync-apply | ✅ Full apply | ⚠️ MVP (list only) |

## 🐛 Troubleshooting

### Command tidak dikenali
```bash
python3 freebuff/freebuff_adapter.py <command> [args]
# atau
Jalankan feature-map <command>
```

### Flow tidak ditemukan
```bash
python3 freebuff/freebuff_adapter.py audit
```

### Commit diblokir
```bash
FEATURE_MAP_ACK=1 git commit -m "message"
```

## 📚 Link

- [README Utama](README.md)
- [CHANGELOG](CHANGELOG.md)
