---
description: Audit konsistensi satu flow bisnis lintas layer berdasarkan FEATURE-MAP.yaml
argument-hint: "[nama-flow | --all]"
---

Kamu menjalankan audit konsistensi flow bisnis berdasarkan registry `FEATURE-MAP.yaml` di root project.

Argumen: `$ARGUMENTS`

## Mode incremental (default, tanpa argumen)

1. Baca `.feature-map/state.json` di root repo (sebelah FEATURE-MAP.yaml).
2. Jika argumen `--all` diberikan ATAU state.json tidak ada → tampilkan daftar
   semua flow (nama, deskripsi singkat, jumlah touchpoint), tanya user flow
   mana yang mau diaudit (atau semuanya), lalu jalankan langkah audit di
   bawah dan lanjut ke "Setelah audit".
3. Jika state ada dan tidak ada flow berstatus `stale` → laporkan
   "[feature-map] Tidak ada flow stale — semua flow clean sejak
   <last_synced_sha>." dan BERHENTI.
4. Jika ada flow stale → audit HANYA flow tersebut (langkah audit di bawah).
   Gunakan `dirty_files` di state sebagai titik awal pemeriksaan.

## Setelah audit

Setelah temuan dilaporkan (atau tidak ada temuan):

1. Ambil SHA HEAD: `git rev-parse HEAD`.
2. Update `.feature-map/state.json`: set setiap flow yang barusan diaudit
   menjadi `{"status": "clean", "dirty_files": [], "marked_at": "<UTC ISO>Z"}`
   dan set `last_synced_sha` ke SHA HEAD. Tulis JSON dengan indent 2.
3. Jika ada temuan GAP yang BELUM diperbaiki user, tanyakan dulu sebelum
   menandai clean — flow dengan gap yang dibiarkan tetap stale.

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
