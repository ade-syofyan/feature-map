"""Native/dependency-free parsing must retain generated policy text exactly."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hooks'))
import feature_map_hook as hook


def test_fallback_decodes_json_escaped_unicode_without_changing_literal_escapes(monkeypatch):
    monkeypatch.setattr(hook, '_parse_feature_map_with_pyyaml', lambda text: None)
    registry = r'''flows:
  billing:
    invariants:
      - "Total adds fee 10 \u603b\u989d\u589e\u52a010"
      - "Keep literal \\u603b and quote \"approved\"."
'''
    assert hook.parse_feature_map(registry)['billing']['invariants'] == [
        'Total adds fee 10 总额增加10', 'Keep literal \\u603b and quote "approved".']
