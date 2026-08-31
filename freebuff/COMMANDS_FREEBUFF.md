# Feature Map Commands - Freebuff Reference

## 📋 Ringkasan Perintah

Ketik perintah berikut di chat Freebuff untuk menjalankan fungsi feature-map:

### 1. Audit Flow
```
Jalankan feature-map audit
```
Atau spesifik:
```
Jalankan feature-map audit partner-registration
```

### 2. Cek Status
```
Jalankan feature-map status
```

### 3. Cek File (PostToolUse)
```
Cek apakah file src/api/partner.py adalah touchpoint feature-map
```

### 4. Init Feature Map
```
Buat FEATURE-MAP.yaml baru untuk project ini
```

### 5. Update Invariants
```
Update invariant flow partner-registration karena ada perubahan validasi
```

### 6. Flow Sync Apply
```
Jalankan feature-map sync apply
```

## 🔧 Script Python

Semua command di atas menggunakan script adapter di:
```
freebuff/freebuff_adapter.py
```

### Jalankan Manual

```bash
# Audit semua flow
python3 freebuff/freebuff_adapter.py audit

# Audit satu flow
python3 freebuff/freebuff_adapter.py audit partner-registration

# Cek status
python3 freebuff/freebuff_adapter.py status

# Cek file (hook)
python3 freebuff/freebuff_adapter.py hook src/api/partner.py
```

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
| Pre-commit | ✅ Otomatis | ⚠️ Manual via agent |

## 📝 Changelog Commands

### v0.12.0 (2026-08-31)
- ✨ Audit command dibuat
- ✨ Status command dibuat
- ✨ Hook command dibuat
- 📝 Dokumentasi commands

### Planned
- [ ] Flow sync apply command
- [ ] Blueprint import command
- [ ] Multi-repo flow command

## 🐛 Troubleshooting Commands

### Command tidak dikenali
```bash
# Gunakan format yang benar
python3 freebuff/freebuff_adapter.py <command> [args]

# Atau ketik di chat
Jalankan feature-map <command>
```

### Flow tidak ditemukan
```bash
# Cek daftar flow
python3 freebuff/freebuff_adapter.py audit

# Pastikan nama flow benar (gunakan kebab-case)
python3 freebuff/freebuff_adapter.py audit partner-registration
```

### File tidak terdeteksi sebagai touchpoint
```bash
# Cek FEATURE-MAP.yaml
cat FEATURE-MAP.yaml

# Pastikan path touchpoint benar
python3 freebuff/freebuff_adapter.py hook src/api/partner.py
```

## 📚 Link Penting

- [README Utama](README.md)
- [CHANGELOG](CHANGELOG.md)
- [Feature Map Original](https://github.com/ade-syofyan/feature-map)
