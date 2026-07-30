---
description: Generate draft FEATURE-MAP.yaml from blueprint, FRD, SRS, SOP, or workflow documents
argument-hint: "<path-dokumen.pdf|txt> [output-path]"
---

Kamu akan membuat draft `FEATURE-MAP.yaml` dari dokumen blueprint/FRD/SRS/SOP/workflow.

Argumen: `$ARGUMENTS`

## Prinsip

1. Dokumen adalah **source of truth awal**, bukan hasil final.
2. Draft harus diberi `confidence: draft`.
3. Setiap flow yang diambil dari dokumen harus menyimpan `evidence` minimal `source`, `page`, dan `section`.
4. Path implementasi awal boleh placeholder (`app/**/payroll/**`, `resources/**/payroll/**`, `database/migrations/**payroll**`) sampai code nyata tersedia.
5. Jangan commit dokumen internal atau output yang berisi data sensitif tanpa izin user.

## Langkah

1. Pastikan path dokumen diberikan. Kalau output path tidak diberikan, pakai `FEATURE-MAP.draft.yaml`.
2. Jalankan importer:

   `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/fm_blueprint.py "<dokumen>" -o "<output>"`

   Jika `pypdf` belum ada untuk PDF, beri tahu user:

   `python3 -m pip install pypdf`

3. Review hasil draft:
   - Flow bisnis yang terdeteksi.
   - Evidence halaman/bagian.
   - Placeholder path yang perlu di-bind ke code nyata.
   - Invariant yang terlalu generik dan harus diperjelas.
4. Laporkan ringkasan ke user dan minta review sebelum mengganti `FEATURE-MAP.yaml`.

## Setelah Code Ada

Saat project sudah punya implementasi, ganti placeholder path dengan file nyata dan jalankan `/feature-map:flow-audit --all`.
