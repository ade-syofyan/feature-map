# feature-map

Plugin Claude Code untuk memetakan **flow bisnis lintas layer/service** — coupling semantik yang tidak terlihat oleh call-graph tools (mis. form pendaftaran di mobile app ↔ halaman verifikasi di web admin).

## Cara kerja

- **`FEATURE-MAP.yaml`** (per project, di root repo) — registry flow bisnis: policy, daftar touchpoint (glob + role), invariants.
- **Hook PostToolUse** — setiap Edit/Write dicocokkan ke touchpoints; kalau match, Claude langsung diberi reminder berisi touchpoint lain + invariants yang harus dijaga.
- **`/flow-audit [nama-flow]`** — audit on-demand: baca semua touchpoint satu flow, laporkan GAP/DRIFT/OK.
- **`/flow-map-init`** — generate draft FEATURE-MAP.yaml untuk project baru.
- **Skill `feature-map`** — aturan perawatan registry.

## Install

```bash
claude plugin marketplace add ~/Documents/MApp/claude-plugins
claude plugin install feature-map@ade-plugins
```

Lalu di tiap project jalankan `/flow-map-init` sekali. Tanpa `FEATURE-MAP.yaml`, hook diam (no-op) — aman dipasang global.

## Catatan skema

Parser hook adalah subset YAML tanpa dependency (tidak butuh PyYAML). Ikuti skema persis seperti di skill/command; jangan pakai anchor, multiline scalar, atau struktur nested lain.
