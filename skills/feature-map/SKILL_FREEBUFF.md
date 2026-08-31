---
name: feature-map-freebuff
description: Feature Map adapter untuk Freebuff - maintained bersama SKILL.md asli
---

# Feature Map - Freebuff Adapter

## Yang Bisa Dijalankan di Freebuff

### ✅ SKILL.md (behavioral guidelines)
Ikuti guideline dari `skills/feature-map/SKILL.md` saat edit file.

### ✅ Hooks (via Agent)
Saat Freebuff mendeteksi file berubah, agent akan:
1. Menjalankan `freebuff/freebuff_adapter.py hook <file>`
2. Menampilkan reminder jika file adalah touchpoint
3. Mengingatkan untuk cek touchpoint lain

### ✅ Commands (via Terminal)
Jalankan command berikut via terminal:
```bash
# Audit flow
python3 freebuff/freebuff_adapter.py audit [flow_name]

# Cek status
python3 freebuff/freebuff_adapter.py status

# Cek file (hook)
python3 freebuff/freebuff_adapter.py hook <file_path>
```

### ✅ FEATURE-MAP.yaml Workflow
1. Baca `skills/feature-map/SKILL.md` untuk panduan lengkap
2. Jalankan `python3 freebuff/freebuff_adapter.py audit` untuk audit
3. Update `FEATURE-MAP.yaml` jika ada perubahan bisnis

## Cara Agent Bekerja di Freebuff

### Saat Edit File
Agent akan mengecek:
1. Apakah file yang diedit ada di touchpoints
2. Jika ya, tampilkan reminder
3. Cek apakah ada perubahan aturan bisnis
4. Sarankan update FEATURE-MAP.yaml jika perlu

### Saat Selesai Task
Agent akan memastikan:
1. Semua touchpoint terkait sudah dicek
2. Invariant masih konsisten
3. Tidak ada gap antara kode dan registry

### Reminder Format
```
[feature-map] File yang baru diedit adalah touchpoint!
📄 File: src/api/partner.py

🔗 Flow: partner-registration
📋 Policy: KTP wajib sebelum verifikasi partner bisa disetujui
📍 Touchpoint lainnya:
   - mobile/**/PartnerRegistrationForm.*
   - src/api/partner.py ← file ini
   - admin/**/PartnerVerificationPage.*
   - docs/api/partner-registration.md

⚠️  Pastikan perubahan konsisten dengan touchpoint lain!
💡 Jika ada perubahan aturan bisnis, update FEATURE-MAP.yaml
```

## Troubleshooting

### Hook tidak jalan
```bash
# Test manual
python3 freebuff/freebuff_adapter.py hook src/test.py
```

### Command tidak dikenali
Gunakan format:
```
Jalankan feature-map <command>
```
Atau:
```
python3 freebuff/freebuff_adapter.py <command>
```

### FEATURE-MAP.yaml tidak terbaca
Pastikan file ada di root project dan formatnya benar.
