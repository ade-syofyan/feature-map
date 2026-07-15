# feature-map

Plugin Claude Code untuk memetakan **flow bisnis lintas layer/service** — coupling semantik yang tidak terlihat oleh call-graph tools (mis. form pendaftaran di mobile app ↔ halaman verifikasi di web admin).

## Cara kerja

- **`FEATURE-MAP.yaml`** (per project, di root repo) — registry flow bisnis: policy, daftar touchpoint (glob + role), invariants.
- **Hook PostToolUse** — setiap Edit/Write dicocokkan ke touchpoints; kalau match, Claude langsung diberi reminder berisi touchpoint lain + invariants yang harus dijaga.
- **`/flow-audit [nama-flow]`** — audit on-demand: baca semua touchpoint satu flow, laporkan GAP/DRIFT/OK.
- **`/flow-map-init`** — generate draft FEATURE-MAP.yaml untuk project baru.
- **Skill `feature-map`** — aturan perawatan registry.

## v0.2.0 — Stale flow detection

- Hook menandai flow `stale` di `.feature-map/state.json` (gitignored) begitu
  touchpoint-nya diedit, atau berubah lewat git (merge/pull/checkout —
  terdeteksi via `git diff <last_synced_sha>..HEAD`).
- `/feature-map:flow-sync-install` memasang git pre-commit hook: peringatan
  (non-blocking) kalau flow berubah di satu layer tapi layer lain tidak ikut.
- `/feature-map:flow-audit` kini incremental: default hanya mengaudit flow
  stale; `--all` untuk audit penuh. Setelah audit, flow ditandai clean dan
  `last_synced_sha` dimajukan ke HEAD.

## Install

```bash
claude plugin marketplace add ~/Documents/MApp/claude-plugins
claude plugin install feature-map@ade-plugins
```

Lalu di tiap project jalankan `/flow-map-init` sekali. Tanpa `FEATURE-MAP.yaml`, hook diam (no-op) — aman dipasang global.

## Catatan skema

Parser hook adalah subset YAML tanpa dependency (tidak butuh PyYAML). Ikuti skema persis seperti di skill/command; jangan pakai anchor, multiline scalar, atau struktur nested lain.
