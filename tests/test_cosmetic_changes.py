"""Synthetic presentation changes stay quiet; data contracts still need review."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hooks'))
import feature_map_hook as hook
import fm_pending
import fm_state


@pytest.fixture
def target(tmp_path):
    (tmp_path / 'FEATURE-MAP.yaml').write_text('''flows:
  invoice:
    confidence: reviewed
    touchpoints:
      - path: "app/Invoice.php"
        role: backend-service
    invariants:
      - "Total includes the declared fee."
''')
    path = tmp_path / 'app/Invoice.php'
    path.parent.mkdir()
    path.write_text('<?php\n')
    return tmp_path, path


def edit(target, old, new):
    root, path = target
    hook.handle({'cwd': str(root), 'tool_name': 'Edit', 'tool_input': {
        'file_path': str(path), 'old_string': old, 'new_string': new}})


@pytest.mark.parametrize('old,new', [
    ('<td class="table-cell p-2 text-left">Total</td>', '<td class="table-cell p-4 text-right">Total</td>'),
    ('<td style="font-size:12px;color:#111">Total</td>', '<td style="font-size:14px;color:#222">Total</td>'),
    ("$sheet->getStyle('A1')->getFont()->setBold(false);", "$sheet->getStyle('A1')->getFont()->setBold(true);"),
    ("$sheet->getColumnDimension('B')->setWidth(18);", "$sheet->getColumnDimension('B')->setWidth(24);"),
])
def test_presentation_only_edit_has_no_reminder_pending_or_stale(target, capsys, old, new):
    edit(target, old, new)
    assert capsys.readouterr().out == ''
    assert fm_pending.load_all_pending(str(target[0])) == {}
    assert fm_state.load_state(str(target[0]))['flows'] == {}


def test_unchanged_formula_in_edit_context_is_not_a_new_formula_change(target, capsys):
    old = '$total = $subtotal + $fee;\n<td class="p-2">Total</td>'
    new = '$total = $subtotal + $fee;\n<td class="p-4">Total</td>'
    assert hook.detect_formula_change('Edit', {'old_string': old, 'new_string': new}) == []
    edit(target, old, new)
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('old,new', [
    ('$total = $subtotal + 7;', '$total = $subtotal + 9;'),
    ("$sheet->setTitle('Batch A');", "$sheet->setTitle('Batch B');"),
    ("$query->where('status', 'active');", "$query->where('status', 'pending');"),
    ('<button class="p-2">Save</button>', '<button class="hidden p-2">Save</button>'),
])
def test_rule_structure_filter_and_visibility_changes_still_need_review(target, capsys, old, new):
    edit(target, old, new)
    assert 'feature-map' in capsys.readouterr().out
    assert 'invoice' in fm_pending.load_all_pending(str(target[0]))


def test_removed_business_condition_is_detected():
    hits = hook.detect_business_condition_change('Edit', {
        'old_string': "if ($item->status === 'active') { return true; }",
        'new_string': 'return true;'})
    assert any('active' in line for line in hits)


def test_cosmetic_edit_does_not_clear_existing_business_pending(target, capsys):
    edit(target, '$total = $subtotal + 7;', '$total = $subtotal + 9;')
    capsys.readouterr()
    before = fm_pending.load_all_pending(str(target[0]))
    edit(target, '<td class="p-2">Total</td>', '<td class="p-4">Total</td>')
    assert capsys.readouterr().out == ''
    assert fm_pending.load_all_pending(str(target[0])) == before


def test_mixed_multiedit_keeps_business_warning(target, capsys):
    root, path = target
    hook.handle({'cwd': str(root), 'tool_name': 'MultiEdit', 'tool_input': {
        'file_path': str(path), 'edits': [
            {'old_string': '<td class="p-2">Total</td>', 'new_string': '<td class="p-4">Total</td>'},
            {'old_string': '$total = $subtotal + 7;', 'new_string': '$total = $subtotal + 9;'}]}})
    text = json.loads(capsys.readouterr().out)['hookSpecificOutput']['additionalContext']
    assert 'RUMUS/KALKULASI BISNIS' in text


def test_class_like_text_in_business_data_is_not_treated_as_markup(target, capsys):
    edit(target, "$label = 'class=\"p-2\"';", "$label = 'class=\"p-4\"';")
    assert 'feature-map' in capsys.readouterr().out
    assert 'invoice' in fm_pending.load_all_pending(str(target[0]))


@pytest.mark.parametrize('attribute', ['data-class', 'data-style'])
def test_custom_data_attributes_are_not_presentation_only(target, capsys, attribute):
    old, new = ('p-2', 'p-4') if attribute == 'data-class' else ('color:red', 'color:blue')
    edit(target, f'<td {attribute}="{old}">Value</td>', f'<td {attribute}="{new}">Value</td>')
    assert 'feature-map' in capsys.readouterr().out
    assert 'invoice' in fm_pending.load_all_pending(str(target[0]))


@pytest.mark.parametrize('zero', ['0.0px', '00px', '.0em', '+0rem', '0.00%'])
def test_zero_font_size_must_remain_reviewable(target, capsys, zero):
    edit(target, '<span style="font-size:12px">Total</span>', f'<span style="font-size:{zero}">Total</span>')
    assert 'feature-map' in capsys.readouterr().out


def test_zero_excel_column_width_must_remain_reviewable(target, capsys):
    edit(target, "$sheet->getColumnDimension('B')->setWidth(18);", "$sheet->getColumnDimension('B')->setWidth(00);")
    assert 'feature-map' in capsys.readouterr().out


@pytest.mark.parametrize('old,new', [
    ('''<input value='Apply class="p-2"'>''', '''<input value='Apply class="p-4"'>'''),
    ('''<input data-filter='Apply style="color:red"'>''', '''<input data-filter='Apply style="color:blue"'>'''),
    ('''<input value='Apply class="p-2" > limit'>''', '''<input value='Apply class="p-4" > limit'>'''),
])
def test_class_or_style_text_inside_other_attribute_values_is_data(target, capsys, old, new):
    edit(target, old, new)
    assert 'feature-map' in capsys.readouterr().out


def test_multiline_attribute_value_is_business_data(target, capsys):
    edit(target, '<input value=\'Apply\n class="p-2"\'>', '<input value=\'Apply\n class="p-4"\'>')
    assert 'feature-map' in capsys.readouterr().out
