---
name: feature-map
description: Use when editing files that belong to a cross-layer business flow, when a business policy changes, or when adding a new feature that spans multiple apps/services — maintains FEATURE-MAP.yaml so related touchpoints stay consistent
---

# Feature Map — Pemetaan Flow Bisnis Lintas Layer

`FEATURE-MAP.yaml` di root project adalah registry flow bisnis yang implementasinya tersebar di beberapa layer/service/app (contoh: pendaftaran mitra = form di mobile app + validasi backend + halaman verifikasi web + Postman docs). Coupling seperti ini semantik — tidak terlihat dari call graph — jadi harus dideklarasikan eksplisit.

## Aturan

1. **Saat reminder hook muncul** (`[feature-map] File yang baru diedit adalah touchpoint ...`): sebelum menganggap task selesai, periksa touchpoint lain yang disebut. Kalau perubahanmu mengubah kontrak/validasi/status yang mereka andalkan, sesuaikan juga atau laporkan gap-nya ke user secara eksplisit.
2. **Saat policy bisnis berubah** (mis. "KTP jadi wajib"): update field `policy` dan `invariants` di flow terkait di `FEATURE-MAP.yaml` dalam commit yang sama.
3. **Saat membuat fitur baru lintas layer**: daftarkan sebagai flow baru di `FEATURE-MAP.yaml` sebelum task dianggap selesai.
4. **Saat memindah/menghapus file touchpoint**: update path glob-nya di registry.
5. Audit menyeluruh satu flow: pakai command `/flow-audit <nama-flow>`. Setup awal di project baru: `/flow-map-init`.

## Skema (subset YAML — jangan pakai anchor, multiline, atau nested lain)

```yaml
flows:
  nama-flow-kebab:
    description: "satu kalimat"
    policy: "kebijakan bisnis saat ini"
    touchpoints:
      - path: "glob/relatif/dari/root/**/File*.kt"
        role: client-form        # client-form|client-view|backend-validation|backend-service|admin-view|docs|db-migration|event-consumer
        note: "opsional"
    invariants:
      - "aturan yang harus konsisten antar touchpoint"
```

Glob dicocokkan terhadap path relatif dari root project (fnmatch; `*` juga match `/`).
