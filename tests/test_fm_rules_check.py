import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import fm_rules_check


def test_extract_pest_descriptions():
    text = """
    it('does not explain missing nrp for office monthly rows', function (): void {
        expect(true)->toBeTrue();
    });
    test('prioritizes iams spv role code for three-day allocations', function (): void {});
    """
    descs = fm_rules_check.extract_test_descriptions(text)
    assert "does not explain missing nrp for office monthly rows" in descs
    assert "prioritizes iams spv role code for three-day allocations" in descs


def test_extract_phpunit_method_names():
    text = """
    public function testOfficeExcludedFromNrpWarning(): void {}
    public function test_kacab_amount_from_spk(): void {}
    """
    descs = fm_rules_check.extract_test_descriptions(text)
    assert any("office" in d and "excluded" in d and "nrp" in d for d in descs)
    assert any("kacab" in d and "amount" in d and "spk" in d for d in descs)


def test_significant_words_drops_stopwords_and_short_tokens():
    words = fm_rules_check.significant_words("does not explain missing nrp for office rows")
    assert "office" in words
    assert "missing" in words
    assert "nrp" in words
    assert "not" not in words
    assert "for" not in words


def test_check_flow_flags_uncovered_test_description(tmp_path):
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests" / "RefundExampleTest.php"
    test_file.write_text(
        "<?php\n"
        "it('does not explain missing nrp for office monthly rows', function (): void {});\n"
    )
    flow = {
        "policy": "Alokasi refund dari master rule ke batch pembayaran",
        "invariants": ["rebuildAllocations wajib diikuti approveAllocationsIfComplete"],
        "touchpoints": [{"path": "tests/RefundExampleTest.php", "role": "backend-validation"}],
    }
    result = fm_rules_check.check_flow(str(tmp_path), "refund-batch-allocation", flow)
    assert result["checked_test_files"] == ["tests/RefundExampleTest.php"]
    assert len(result["possible_undocumented_rules"]) == 1
    assert "office" in result["possible_undocumented_rules"][0]["unmatched_terms"]


def test_check_flow_does_not_flag_when_invariant_covers_it(tmp_path):
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests" / "RefundExampleTest.php"
    test_file.write_text(
        "<?php\n"
        "it('does not explain missing nrp for office monthly rows', function (): void {});\n"
    )
    flow = {
        "policy": "",
        "invariants": [
            "Office tidak boleh kena warning NRP kosong pada baris alokasi bulanan apapun",
        ],
        "touchpoints": [{"path": "tests/RefundExampleTest.php", "role": "backend-validation"}],
    }
    result = fm_rules_check.check_flow(str(tmp_path), "refund-batch-allocation", flow)
    assert result["possible_undocumented_rules"] == []


def test_check_flow_ignores_non_test_touchpoints(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "Controller.php").write_text("<?php\nclass Controller {}\n")
    flow = {
        "policy": "",
        "invariants": [],
        "touchpoints": [{"path": "app/Controller.php", "role": "backend-service"}],
    }
    result = fm_rules_check.check_flow(str(tmp_path), "some-flow", flow)
    assert result["checked_test_files"] == []
    assert result["possible_undocumented_rules"] == []
