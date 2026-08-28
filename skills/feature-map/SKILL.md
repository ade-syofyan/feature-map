---
name: feature-map
description: Use when editing files that belong to a cross-layer business flow, when a business policy changes, or when adding a new feature that spans multiple apps/services — maintains FEATURE-MAP.yaml so related touchpoints stay consistent
---

# Feature Map — Pemetaan Flow Bisnis Lintas Layer

`FEATURE-MAP.yaml` di root project adalah registry flow bisnis yang implementasinya tersebar di beberapa layer/service/app (contoh: pendaftaran mitra = form di mobile app + validasi backend + halaman verifikasi web + Postman docs). Coupling seperti ini semantik — tidak terlihat dari call graph — jadi harus dideklarasikan eksplisit.

## Aturan

1. **Saat reminder hook muncul** (`[feature-map] File yang baru diedit adalah touchpoint ...`): sebelum menganggap task selesai, periksa touchpoint lain yang disebut. Kalau perubahanmu mengubah kontrak/validasi/status yang mereka andalkan, sesuaikan juga atau laporkan gap-nya ke user secara eksplisit.
2. **Saat policy bisnis berubah** (mis. "KTP jadi wajib"): update field `policy` dan `invariants` di flow terkait di `FEATURE-MAP.yaml` dalam commit yang sama.
   - **Rumus/kalkulasi juga policy.** Kalau perubahanmu menambah/mengubah rumus perhitungan, threshold, atau kondisi bisnis (bukan cuma nama variabel/refactor) — tulis rumus lengkapnya (operand & urutan operasi, bukan cuma nama fungsi) sebagai invariant baru. Ini berlaku bahkan kalau task-nya cuma "audit", "cek", atau "perbaiki bug" — **jangan tunggu user bertanya "apakah ini sudah dicatat?" dulu**, itu berarti sudah kelewat.
   - Kalau reminder hook menyertakan baris `⚠ RUMUS/KALKULASI BISNIS terdeteksi`, itu heuristik otomatis (bisa false positive) — verifikasi apakah baris yang dicurigai memang rumus bisnis, dan kalau ya langsung tulis invariant-nya sebelum lanjut ke perubahan berikutnya, jangan ditunda sampai akhir sesi.
3. **Saat membuat fitur baru lintas layer**: daftarkan sebagai flow baru di `FEATURE-MAP.yaml` sebelum task dianggap selesai.
4. **Saat memindah/menghapus file touchpoint**: update path glob-nya di registry.
5. Audit menyeluruh satu flow: pakai command `/feature-map:flow-audit <nama-flow>`. Setup awal di project baru: `/feature-map:flow-map-init`.
6. **Kalau ada reminder `[feature-map] N flow(s) have pending drift...`** di
   akhir turn: jalankan `/feature-map:flow-sync-apply` untuk merangkum
   perubahan jadi invariant/policy baru di `FEATURE-MAP.yaml` sebelum
   menganggap task selesai — kecuali perubahannya memang bukan perubahan
   aturan bisnis (refactor murni, rename, format), dalam hal ini boleh
   dilewati.
7. Untuk mengubah blueprint/FRD/SRS/SOP/workflow menjadi draft registry, pakai `/feature-map:flow-map-from-doc <dokumen> [output]`; hasilnya wajib direview sebelum mengganti `FEATURE-MAP.yaml`.
8. Kalau flow yang diedit punya touchpoint test, `/feature-map:flow-audit` otomatis cross-check deskripsi test terhadap invariant yang ada (lewat `hooks/fm_rules_check.py`) dan melaporkan kategori **RULE-GAP** kalau ada rule yang sudah ada di test tapi belum di invariant — regression test sering menyebut edge case (role tertentu dikecualikan, nilai dihitung dari sumber lain) lebih dulu daripada registry-nya diupdate.
9. **Kalau "cara main"/aturan bisnis-nya kompleks** (banyak mode/varian, rumus dengan beberapa kondisi, banyak edge case seperti kasus rekap presensi sales — mode default vs sales, formula Sanksi vs Tidak Hadir, pengecualian per jabatan, aturan khusus tipe Mitra, dst) — satu baris `invariants:` tidak cukup. Buat dokumen markdown terpisah (`docs/flows/<nama-flow>.md`, atau lokasi lain yang masuk akal di project itu) berisi narasi lengkap: cara kerja tiap mode, rumus dengan contoh angka nyata, tabel perbandingan varian, dan kondisi pengecualian. Daftarkan path-nya di field `mechanics_doc` flow tsb. `invariants:` di YAML tetap wajib diisi (ringkasan cepat untuk reminder hook), `mechanics_doc` adalah pelengkap untuk detail yang tidak muat di satu baris.
   - Update `mechanics_doc` di commit yang sama saat rumus/mode/pengecualian berubah — jangan biarkan dokumen itu basi sementara `invariants:` sudah diupdate (atau sebaliknya).

## Skema (subset YAML — jangan pakai anchor, multiline, atau nested lain)

```yaml
flows:
  nama-flow-kebab:
    description: "satu kalimat"
    confidence: draft          # draft|reviewed|approved
    policy: "kebijakan bisnis saat ini"
    business_aspects:
      - status              # formula|status|validation|permission|eligibility|visibility|report|export|notification|scheduler|migration
      - validation
    mechanics_doc: "docs/flows/nama-flow-kebab.md"   # opsional, lihat aturan #8
    last_reviewed: "2026-07-30 (a1b2c3d)"            # opsional, diisi otomatis oleh flow-sync-apply
    evidence:
      - source: "docs/blueprint.pdf"
        page: 12
        section: "WORKFLOW ABSENSI"
    touchpoints:
      - path: "glob/relatif/dari/root/**/File*.kt"
        role: client-form        # client-form|client-view|backend-validation|backend-service|admin-view|data-schema|docs|db-migration|event-consumer
        note: "opsional"
    invariants:
      - "aturan yang harus konsisten antar touchpoint"
    history:
      - date: "2026-07-30"
        sha: "a1b2c3d"
        author: "Ade Syofyan"
        change: "Sanksi: potongan 5% jadi 10% per hari tidak hadir tanpa keterangan"
```

Glob dicocokkan terhadap path relatif dari root project (fnmatch; `*` juga match `/`).

`confidence` dan `evidence` opsional, tapi disarankan untuk flow yang berasal dari dokumen enterprise. `draft` berarti hasil importer belum divalidasi ke code nyata.

`mechanics_doc` opsional — path relatif dari root project ke markdown yang menjelaskan "cara main dan aturan main" flow tsb secara naratif (lihat aturan #8). Isi dokumen itu bebas formatnya, tapi minimal sebaiknya punya: ringkasan tiap mode/varian, rumus lengkap dengan contoh angka nyata (bukan cuma nama variabel), dan daftar pengecualian/edge case beserta alasannya.

`business_aspects` opsional — tag ringan untuk jenis aturan bisnis yang wajib diaudit, bukan lokasi file. Pakai saat flow punya logic yang gampang kelewat: `formula`, `status`, `validation`, `permission`, `eligibility`, `visibility`, `report`, `export`, `notification`, `scheduler`, `migration`. Contoh: frontend yang menyembunyikan tombol berdasarkan status pakai `visibility` + `status`; engine payroll pakai `formula`; reminder email pakai `notification` + `scheduler`.

`last_reviewed` opsional — jejak audit ringkas "siapa pun yang menyentuh flow ini terakhir kali sadar dan menyetujui perubahan aturan bisnisnya". Diisi otomatis oleh `/feature-map:flow-sync-apply` (tanggal + short SHA commit saat itu, kalau tersedia) setiap kali invariant/policy flow tsb disinkronkan — bukan mekanisme approval terpisah, cuma catatan hasil dari approval Edit yang sudah terjadi. Berguna untuk orang baru: kalau field ini basi dibanding riwayat commit touchpoint-nya, berarti ada perubahan yang belum tercatat sadar oleh siapa pun.

`history` opsional — riwayat historis penuh perubahan aturan bisnis flow ini, satu entry per sinkronisasi lewat `/feature-map:flow-sync-apply`: `date`, `sha` (short SHA, atau "uncommitted" kalau belum ada commit), `author` (dari `git config user.name`), dan `change` (ringkasan "dari apa ke apa", bukan cuma "invariant diupdate"). Selalu **append**, jangan pernah menghapus/menimpa entry lama — ini catatan "sebelumnya apa, jadi apa, siapa pelakunya, kapan" untuk siapa pun yang pegang flow ini nanti tanpa harus menelusuri `git log` satu-satu di banyak file touchpoint.
