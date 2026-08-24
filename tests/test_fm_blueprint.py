import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import fm_blueprint


def test_extract_workflows_from_text_pages():
    pages = [
        (7, "3. WORKFLOW CONTRACT MANAGEMENT Input: Kontrak client. Proses: Upload Dokumen Kontrak ↓ Legal Review ↓ Finance Review ↓ Direktur Approval ↓ Contract Active Output: Database kontrak."),
        (8, "9. WORKFLOW ABSENSI Input: Employee ↓ Check In ↓ GPS Verification ↓ Face Photo ↓ Check Out Sistem: Menghitung kehadiran, keterlambatan, lembur."),
    ]

    flows = fm_blueprint.extract_workflows(pages, "blueprint.pdf")

    assert [f["slug"] for f in flows] == ["contract-management", "absensi"]
    assert flows[0]["page"] == 7
    assert "Kontrak client" in flows[0]["terms"][0]


def test_generate_feature_map_from_text_file(tmp_path):
    doc = tmp_path / "blueprint.txt"
    doc.write_text(
        "WORKFLOW PAYROLL Proses: Attendance Data ↓ Payroll Calculation. "
        "Output: Slip gaji dan laporan payroll.",
        encoding="utf-8",
    )

    rendered = fm_blueprint.generate_feature_map(str(doc), "docs/blueprint.txt")

    assert "payroll:" in rendered
    assert "confidence: draft" in rendered
    assert "evidence:" in rendered
    assert 'source: "docs/blueprint.txt"' in rendered
    assert 'path: "app/**/payroll/**"' in rendered


def test_read_pages_missing_document_fails_with_clear_message(tmp_path):
    missing = tmp_path / "missing.txt"

    with pytest.raises(SystemExit, match="Document not found"):
        fm_blueprint.read_pages(str(missing))
