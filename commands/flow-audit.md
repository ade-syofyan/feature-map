---
description: Audit konsistensi satu flow bisnis lintas layer berdasarkan FEATURE-MAP.yaml
argument-hint: "[nama-flow]"
---

Kamu menjalankan audit konsistensi flow bisnis berdasarkan registry `FEATURE-MAP.yaml` di root project.

Argumen: `$ARGUMENTS`

## Kalau tanpa argumen

Baca `FEATURE-MAP.yaml`, tampilkan daftar semua flow (nama, deskripsi singkat, jumlah touchpoint), lalu tanya user flow mana yang mau diaudit.

## Kalau ada nama flow

1. Baca entry flow tersebut dari `FEATURE-MAP.yaml`: policy, touchpoints, invariants.
2. Baca **semua file touchpoint** (resolve glob-nya dulu). Kalau ada glob yang tidak match file apa pun, laporkan sebagai touchpoint mati (file dipindah/dihapus — registry perlu diupdate).
3. Bandingkan implementasi antar touchpoint terhadap policy dan tiap invariant. Fokus pada:
   - Validasi field: field yang wajib/opsional harus konsisten antara client form, backend validation, dan tampilan admin/verifikasi.
   - Enum/status: nilai status yang dikenal tiap sisi harus sama.
   - Kontrak API: request/response yang dipakai client vs yang diexpose backend vs yang terdokumentasi (mis. Postman collection).
   - Copy/label UI yang menjanjikan perilaku tertentu vs perilaku backend sebenarnya.
4. Laporkan hasil sebagai daftar temuan, urut dari paling kritis:
   - **GAP** — inkonsistensi nyata yang bisa bikin bug/stuck user (sebutkan file:line kedua sisi)
   - **DRIFT** — belum bug, tapi registry/dokumentasi sudah tidak akurat
   - **OK** — invariant yang terverifikasi konsisten
5. Jangan langsung memperbaiki — audit ini deliverable-nya laporan. Tawarkan perbaikan setelah user melihat temuan.
