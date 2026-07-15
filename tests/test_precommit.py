import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_hook as hook
import precommit_check

FM = """flows:
  checkout:
    description: "alur checkout"
    touchpoints:
      - path: "app/checkout/*.py"
        role: backend
      - path: "lib/screens/checkout/*.dart"
        role: mobile
"""


def flows():
    return hook.parse_feature_map(FM)


def test_warns_when_one_role_touched_other_untouched():
    warnings = precommit_check.check(flows(), staged=["app/checkout/cart.py"],
                                     changed_since_sync=["app/checkout/cart.py"])
    assert len(warnings) == 1
    assert "checkout" in warnings[0]
    assert "mobile" in warnings[0]


def test_silent_when_both_roles_staged():
    warnings = precommit_check.check(
        flows(),
        staged=["app/checkout/cart.py", "lib/screens/checkout/cart.dart"],
        changed_since_sync=["app/checkout/cart.py", "lib/screens/checkout/cart.dart"])
    assert warnings == []


def test_silent_when_other_role_changed_since_sync():
    # layer lain sudah diubah di commit sebelumnya (belum di-audit) — jangan berisik
    warnings = precommit_check.check(
        flows(), staged=["app/checkout/cart.py"],
        changed_since_sync=["app/checkout/cart.py", "lib/screens/checkout/cart.dart"])
    assert warnings == []


def test_silent_when_no_touchpoint_staged():
    warnings = precommit_check.check(flows(), staged=["README.md"],
                                     changed_since_sync=["README.md"])
    assert warnings == []
