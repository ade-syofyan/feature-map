---
description: Rangkum drift bisnis yang tertunda jadi invariant/policy baru di FEATURE-MAP.yaml
---

Sinkronkan drift flow bisnis yang tertunda (dicatat otomatis oleh PostToolUse
hook feature-map di `.claude/feature-map-pending/`) ke `FEATURE-MAP.yaml`.
Langkah:

1. Tentukan root project: cari `FEATURE-MAP.yaml` mulai dari cwd naik ke
   parent (sama seperti hook lain di plugin ini). Kalau tidak ada, beri tahu
   user dan berhenti.
2. List file pending:
   `python3 -c "import sys; sys.path.insert(0,'<CLAUDE_PLUGIN_ROOT>/hooks'); import fm_pending, json; print(json.dumps(fm_pending.load_all_pending('<root>')))"`
   Kalau hasilnya `{}`, beri tahu user "tidak ada drift tertunda" dan
   berhenti.
3. Untuk tiap `flow_id` di hasil pending: baca entry-nya (`file`, `role`,
   `tool_name`, `diff`, `formula_snippets`, `condition_snippets`, `current_policy`,
   `current_invariants`, `current_mechanics_doc`) dan baca blok flow yang
   sesuai di `FEATURE-MAP.yaml` saat ini (bisa saja sudah berubah sejak
   entry dicatat — pakai isi file `FEATURE-MAP.yaml` sekarang sebagai
   sumber kebenaran, `current_*` di entry pending cuma konteks "apa yang
   sudah tercatat waktu edit terjadi").
4. Nilai: apakah `diff` ini benar-benar perubahan aturan bisnis (formula,
   threshold, validasi, kondisi kelayakan, status, permission, atau visibility UI) — atau cuma refactor/rename/
   format non-semantik? Kalau non-semantik: laporkan sebagai "dilewati,
   bukan perubahan aturan bisnis", lalu hapus file pending-nya juga (lihat
   perintah di langkah 7 — dipakai sama untuk path sync maupun skip) dan
   lanjut ke flow_id berikutnya. Tidak ada yang hilang: kalau nanti file
   touchpoint ini diedit lagi, PostToolUse hook akan menulis ulang file
   pending dengan diff yang baru, jadi tidak perlu menyisakan entry lama
   supaya Stop hook berhenti mengingatkan drift yang sudah diputuskan.
5. Kalau memang perubahan aturan bisnis: rangkum jadi kalimat
   `invariants:` baru (revisi kalau menggantikan aturan lama, tambahan
   kalau melengkapi) dan, kalau relevan, update `policy:`. Kalau
   `formula_snippets`/`condition_snippets` di entry menunjukkan rumus atau kondisi kompleks
   (banyak mode/kondisi) dan flow itu belum punya `mechanics_doc`, pertimbangkan
   sarankan (bukan buat otomatis) dokumen `docs/flows/<flow_id>.md`
   mengikuti aturan #9 di SKILL.md.
6. Terapkan perubahan dengan tool Edit langsung ke `FEATURE-MAP.yaml`. Di
   Edit yang sama:
   - Set/update field `last_reviewed` untuk flow tsb, isi dengan tanggal
     hari ini + short SHA dari `git rev-parse --short HEAD` (kalau
     gagal/belum ada commit, tulis "uncommitted") — contoh:
     `last_reviewed: "2026-07-30 (a1b2c3d)"`.
   - **Append** (jangan pernah hapus/timpa entry lama) satu entry baru ke
     `history:` flow tsb dengan field `date` (hari ini), `sha` (short SHA
     dari `git rev-parse --short HEAD`, atau "uncommitted"), `author` (dari
     `git config user.name`), dan `change` — ringkasan konkret "dari apa
     jadi apa" (mis. "Sanksi: potongan 5% jadi 10% per hari tidak hadir
     tanpa keterangan"), bukan cuma "invariant diupdate". Kalau flow belum
     punya key `history:`, buat baru.
   Ini bukan gate baru, cuma mencatat bahwa perubahan aturan bisnisnya
   sudah lewat approval Edit di langkah ini. Prompt persetujuan Edit dari
   Claude Code itu sendiri tetap satu-satunya review gate — jangan buat
   mekanisme konfirmasi terpisah.
7. Setelah flow tsb selesai diproses (baik disinkronkan lewat Edit di
   langkah 6, maupun dilewati di langkah 4 karena non-semantik), hapus
   file pending-nya:
   `python3 -c "import sys; sys.path.insert(0,'<CLAUDE_PLUGIN_ROOT>/hooks'); import fm_pending; fm_pending.clear_pending('<root>', '<flow_id>')"`
8. Setelah semua flow diproses, laporkan ringkasan ke user: flow mana yang
   disinkronkan (dengan ringkasan perubahan), flow mana yang dilewati dan
   kenapa.
