---
description: Daftarkan repo ini ke registry multi-repo feature-map
argument-hint: "[nama | --list | --remove <nama>]"
---

Kelola registry repo feature-map di `~/.claude/feature-maps/registry.json`
(format: `{"repos": {"<nama>": "<path-absolut>"}}`).

Argumen: `$ARGUMENTS`

1. `--list` → baca registry (kalau tidak ada, anggap kosong), tampilkan
   tabel nama → path, tandai path yang sudah tidak ada di disk. Berhenti.
2. `--remove <nama>` → hapus entri itu dari `repos`, tulis kembali dengan
   indent 2, laporkan. Berhenti.
3. Tanpa argumen atau dengan `<nama>`:
   a. Cari root repo: `git rev-parse --show-toplevel`; kalau bukan git repo,
      pakai direktori yang berisi FEATURE-MAP.yaml terdekat; kalau dua-duanya
      tidak ada, beri tahu user dan berhenti.
   b. Nama = argumen, atau default basename root (lowercase, spasi → `-`).
   c. Buat direktori `~/.claude/feature-maps/` bila perlu, tulis/timpa
      `repos[<nama>] = <root>` dengan indent 2.
   d. Tampilkan isi registry terbaru dan ingatkan: touchpoint di repo lain
      merujuk nama ini lewat field `repo: <nama>` di FEATURE-MAP.yaml.
