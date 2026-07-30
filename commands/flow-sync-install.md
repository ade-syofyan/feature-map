---
description: Pasang git pre-commit hook feature-map (peringatan konsistensi lintas layer)
---

Pasang pre-commit hook feature-map di repo saat ini. Langkah:

1. Pastikan ini git repo (`git rev-parse --git-dir`); kalau bukan, beri tahu
   user dan berhenti.
2. Pastikan FEATURE-MAP.yaml ada di root repo; kalau belum, sarankan
   `/feature-map:flow-map-init` dulu dan berhenti.
3. Tentukan path skrip: `${CLAUDE_PLUGIN_ROOT}/hooks/precommit_check.py`.
4. Baris pemanggilan yang dipasang (append-safe):

   `python3 "<path-precommit_check.py>" || true  # feature-map`

   - Jika `.git/hooks/pre-commit` belum ada: buat file baru berisi
     `#!/bin/sh` + baris di atas, lalu `chmod +x`.
   - Jika sudah ada: kalau sudah mengandung `# feature-map`, laporkan
     "sudah terpasang" dan berhenti. Kalau belum, append baris di atas di
     akhir file (jangan menimpa isi lain, mis. hook code-review-graph).
5. Verifikasi: jalankan `python3 <path> < /dev/null` — harus exit 0 tanpa
   error, lalu laporkan ke user bahwa hook terpasang dengan sifat:
   - Warning cross-role touchpoint (heuristik path) — tidak memblokir commit.
   - Pending drift bisnis (rumus/kondisi terdeteksi, belum disync ke
     FEATURE-MAP.yaml) — **memblokir commit** (exit 1) kecuali jalankan
     `/feature-map:flow-sync-apply` dulu atau override dengan
     `FEATURE_MAP_ACK=1 git commit ...`.
