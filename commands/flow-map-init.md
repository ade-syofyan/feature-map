---
description: Generate draft FEATURE-MAP.yaml untuk project ini dengan mengeksplor codebase
argument-hint: "[fokus flow tertentu, opsional]"
---

Kamu akan membuat (atau memperluas) `FEATURE-MAP.yaml` di root project ini — registry flow bisnis lintas layer untuk plugin feature-map.

Argumen (fokus opsional): `$ARGUMENTS`

## Langkah

1. Kalau `FEATURE-MAP.yaml` sudah ada, baca dulu — mode-mu adalah menambah/memperbaiki, bukan menimpa.
2. Eksplor project: baca README/dokumen arsitektur/roadmap kalau ada, lihat struktur direktori level atas. Identifikasi flow bisnis yang implementasinya **tersebar di lebih dari satu layer/service/app** — itulah kandidat flow (contoh umum: registrasi + verifikasi admin, order lifecycle, pembayaran/wallet, upload & review dokumen).
3. Untuk tiap flow (mulai dari 3–5 yang paling kritis), temukan touchpoint konkretnya via search: file client form/screen, controller/service backend, halaman admin/web, file dokumentasi API. Verifikasi path-nya benar-benar ada.
4. Tulis `FEATURE-MAP.yaml` mengikuti skema PERSIS ini (parser hook-nya subset YAML, jangan pakai fitur YAML lain seperti anchor/multiline):

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

   Role yang disarankan: `client-form`, `client-view`, `backend-validation`, `backend-service`, `admin-view`, `docs`, `db-migration`, `event-consumer`.
5. Tunjukkan draft ke user untuk direview sebelum dianggap final. Ingatkan bahwa hook reminder aktif otomatis begitu file ini ada di root project.
