---
description: Generate draft FEATURE-MAP.yaml untuk project ini dengan mengeksplor codebase
argument-hint: "[fokus flow tertentu, opsional]"
---

Kamu akan membuat (atau memperluas) `FEATURE-MAP.yaml` di root project ini — registry flow bisnis lintas layer untuk plugin feature-map.

Argumen (fokus opsional): `$ARGUMENTS`

## Langkah

1. Kalau `FEATURE-MAP.yaml` sudah ada, baca dulu — mode-mu adalah menambah/memperbaiki, bukan menimpa.
2. **Enumerasi penuh dulu, jangan sampling.** List SEMUA direktori/namespace level modul di layer entrypoint (mis. semua folder di bawah `app/Http/Controllers/`, semua route group, semua service/app di monorepo, semua top-level folder Livewire/screen). Tulis daftar ini eksplisit sebagai checklist kerja sebelum lanjut — jangan langsung lompat ke contoh yang paling familiar/menonjol. Community/module grouping dari code-review-graph (`get_architecture_overview`/`list_communities`) biasanya terlalu kasar untuk ini (satu community bisa menggabung ratusan file lintas fitur) — pakai sebagai referensi arsitektur, bukan sebagai daftar kandidat flow.
3. **Tidak ada filtering/skip di sini — setiap item di checklist harus jadi entri flow.** Ini registry lengkap semua flow bisnis app, bukan cuma yang lintas layer paling mencolok. Untuk tiap item, tentukan touchpoint-nya di semua layer yang ada: client form/screen, backend validation/service, admin/web view, docs, db migration, event consumer — kalau memang cuma ada di satu layer (mis. CRUD admin murni), tulis apa adanya dengan touchpoint yang ada saja, jangan dibuang dari registry. Yang boleh tidak didaftarkan sebagai flow terpisah hanya infrastruktur murni yang bukan flow bisnis (mis. util/helper generik, config framework, health-check) — bukan berdasarkan "kurang kritis" atau "cuma satu layer".
4. Untuk tiap flow, temukan touchpoint konkretnya via search: file client form/screen, controller/service backend, halaman admin/web, file dokumentasi API. Verifikasi path-nya benar-benar ada. Kalau ada beberapa modul kecil yang secara fungsional adalah satu mesin/pipeline yang sama (mis. beberapa master data yang semuanya jadi variabel dari satu formula engine), gabung jadi satu flow umbrella dengan banyak touchpoint — jangan dibuat flow terpisah per file kalau granularitasnya lebih baik di level pipeline.
5. Tulis `FEATURE-MAP.yaml` mengikuti skema PERSIS ini (parser hook-nya subset YAML, jangan pakai fitur YAML lain seperti anchor/multiline):

```yaml
flows:
  nama-flow-kebab:
    description: "satu kalimat"
    policy: "kebijakan bisnis yang berlaku saat ini"
    touchpoints:
      - path: "glob/relatif/dari/root/**/File*.kt"
        role: client-form
        note: "opsional, konteks singkat"
      - path: "service/src/**/SomethingController.kt"
        role: backend-validation
    invariants:
      - "aturan yang harus konsisten antar touchpoint"
```

   Role yang disarankan: `client-form`, `client-view`, `backend-validation`, `backend-service`, `admin-view`, `data-schema`, `docs`, `db-migration`, `event-consumer`.
6. Kalau saat mapping ketemu flow yang rule bisnisnya kompleks (banyak mode/varian, rumus dengan beberapa kondisi, banyak pengecualian) — jangan dipaksa muat ke satu baris `invariants:`. Tambahkan `mechanics_doc: "docs/flows/<nama-flow>.md"` dan siapkan draft dokumen naratifnya (lihat SKILL.md aturan #8) sebagai bagian dari draft ini juga.
7. Tunjukkan draft ke user untuk direview sebelum dianggap final, sertakan ringkasan cakupan: total modul di checklist langkah 2 vs total flow yang berhasil didaftarkan — harus 1:1 (kecuali item yang memang murni infrastruktur non-bisnis, sebutkan itemnya). Ingatkan bahwa hook reminder aktif otomatis begitu file ini ada di root project.
