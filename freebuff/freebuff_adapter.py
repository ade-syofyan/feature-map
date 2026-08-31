#!/usr/bin/env python3
"""
Freebuff Adapter for feature-map plugin.
Menyediakan hook dan command yang kompatibel dengan Freebuff.
"""
import os
import re
import sys
import json
import glob as globmod
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Glob matching – repo-style semantics
# ---------------------------------------------------------------------------
# - `*`   matches within ONE directory segment (no slash)
# - `**`  matches ANY number of segments (including zero)
# - `?`   matches exactly one non-slash char
#
# `fnmatch` is NOT suitable because `*` matches `/` and `**` is not
# handled.  We implement a segment-based matcher instead.
# ---------------------------------------------------------------------------

def _split_segments(pattern):
    """Split a glob pattern into path segments, recognising **."""
    segments = []
    for part in pattern.split('/'):
        segments.append(part)
    return segments


def match_repo_glob(filepath, pattern):
    """Match *filepath* against a repo-style glob *pattern*.

    Rules
    -----
    - ``*``   matches any chars except ``/``
    - ``**``  matches zero or more full path segments
    - ``?``   matches exactly one char except ``/``
    - Literal chars are compared directly
    """
    fp_segs = filepath.split('/')
    pat_segs = _split_segments(pattern)
    return _match_segments(fp_segs, pat_segs, 0, 0)


def _match_segments(fp, pat, fi, pi):
    """Recursive segment matcher with ** support."""
    # Both exhausted → match
    if pi == len(pat) and fi == len(fp):
        return True
    # Pattern exhausted but path still has segments → no match
    if pi == len(pat):
        return False

    seg = pat[pi]

    if seg == '**':
        # ** can skip 0..N path segments
        # Try consuming 0 segments first (stay on same **), then 1, 2, …
        for skip in range(len(fp) - fi + 1):
            if _match_segments(fp, pat, fi + skip, pi + 1):
                return True
        return False
    else:
        # Path exhausted but pattern still has non-** segments → no match
        if fi == len(fp):
            return False
        # fnmatch handles *, ?, and literal chars within one segment
        import fnmatch
        if fnmatch.fnmatch(fp[fi], seg):
            return _match_segments(fp, pat, fi + 1, pi + 1)
        return False


# ---------------------------------------------------------------------------
# YAML inline-comment stripper
# ---------------------------------------------------------------------------

def _strip_inline_comment(line):
    """Remove inline comment from a YAML line, respecting quoted strings.

    Example:
        path: "src/*.py" # comment  →  path: "src/*.py"
        path: 'foo' # bar           →  path: 'foo'
        policy: "no #hash here"     →  policy: "no #hash here"
    """
    in_single = False
    in_double = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '\\' and (in_single or in_double):
            i += 2
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == '#' and not in_single and not in_double:
            return line[:i].rstrip()
        i += 1
    return line


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class FreebuffFeatureMapAdapter:
    """Adapter untuk menjalankan feature-map di Freebuff"""

    def __init__(self, project_root=None):
        self.project_root = project_root or os.getcwd()
        self.feature_map_path = os.path.join(self.project_root, 'FEATURE-MAP.yaml')

    # ----- parser -----

    def parse_feature_map(self):
        """Parse FEATURE-MAP.yaml tanpa PyYAML, handling inline comments."""
        if not os.path.exists(self.feature_map_path):
            return {}

        flows = {}
        current_flow = None
        current_section = None

        with open(self.feature_map_path, 'r') as f:
            for line in f:
                # Strip inline comments BEFORE any processing
                line = _strip_inline_comment(line)
                stripped = line.rstrip()
                indent = len(line) - len(line.lstrip())

                # Detect flow definition (2-space indent)
                if (indent == 2 and ':' in stripped
                        and not stripped.strip().startswith('-')
                        and not stripped.strip().startswith('#')):
                    flow_name = stripped.strip().rstrip(':').strip()
                    if flow_name:
                        current_flow = flow_name
                        flows[current_flow] = {
                            'touchpoints': [],
                            'invariants': [],
                            'policy': '',
                            'business_aspects': [],
                            'confidence': 'draft'
                        }
                        current_section = None
                        continue

                if not current_flow:
                    continue

                # Detect sections (4-space indent)
                if indent == 4:
                    s = stripped.strip()
                    if s == 'touchpoints:':
                        current_section = 'touchpoints'
                        continue
                    elif s == 'invariants:':
                        current_section = 'invariants'
                        continue
                    elif s == 'business_aspects:':
                        current_section = 'business_aspects'
                        continue
                    elif s == 'history:':
                        current_section = 'history'
                        continue
                    elif 'policy:' in s:
                        policy = s.split('policy:', 1)[1].strip().strip('"').strip("'")
                        flows[current_flow]['policy'] = policy
                        current_section = None
                        continue
                    elif 'confidence:' in s:
                        conf = s.split('confidence:', 1)[1].strip()
                        flows[current_flow]['confidence'] = conf
                        current_section = None
                        continue
                    elif 'mechanics_doc:' in s:
                        current_section = None
                        continue
                    elif 'description:' in s:
                        current_section = None
                        continue

                # Parse based on section
                if current_section == 'touchpoints' and indent == 6 and 'path:' in stripped:
                    path = stripped.split('path:', 1)[1].strip().strip('"').strip("'")
                    flows[current_flow]['touchpoints'].append(path)
                elif current_section == 'invariants' and indent == 6 and stripped.strip().startswith('- '):
                    inv = stripped.strip()[2:].strip().strip('"').strip("'")
                    flows[current_flow]['invariants'].append(inv)
                elif current_section == 'business_aspects' and indent == 6 and stripped.strip().startswith('- '):
                    aspect = stripped.strip()[2:].strip()
                    flows[current_flow]['business_aspects'].append(aspect)
                elif current_section == 'history':
                    continue

        return flows

    # ----- matching -----

    def match_touchpoint(self, filepath, pattern):
        """Match filepath against a repo-style glob pattern."""
        return match_repo_glob(filepath, pattern)

    def match_flows(self, flows, files):
        """Find flows that match given files."""
        matched = set()
        for flow_name, flow_data in flows.items():
            for tp in flow_data['touchpoints']:
                for f in files:
                    if self.match_touchpoint(f, tp):
                        matched.add(flow_name)
        return matched

    # ----- hook -----

    def check_file(self, filepath):
        """Cek apakah file adalah touchpoint."""
        flows = self.parse_feature_map()
        relative_path = os.path.relpath(filepath, self.project_root)

        matched = []
        for flow_name, flow_data in flows.items():
            for tp in flow_data['touchpoints']:
                if self.match_touchpoint(relative_path, tp):
                    matched.append({
                        'flow': flow_name,
                        'touchpoints': flow_data['touchpoints'],
                        'invariants': flow_data['invariants'],
                        'policy': flow_data['policy']
                    })
        return relative_path, matched

    def generate_reminder(self, filepath, matched_flows):
        """Generate reminder untuk Freebuff."""
        if not matched_flows:
            return None

        lines = ["[feature-map] Reminder: File yang diedit adalah touchpoint!"]
        lines.append(f"📄 File: {filepath}\n")

        for flow in matched_flows:
            lines.append(f"🔗 Flow: {flow['flow']}")
            if flow['policy']:
                lines.append(f"📋 Policy: {flow['policy']}")
            lines.append("📍 Touchpoint lainnya:")
            for tp in flow['touchpoints']:
                marker = " ← file ini" if tp == filepath else ""
                lines.append(f"   - {tp}{marker}")
            if flow['invariants']:
                lines.append("⚖️  Invariants:")
                for inv in flow['invariants']:
                    lines.append(f"   - {inv}")
            lines.append("")

        lines.append("⚠️  Pastikan perubahan konsisten dengan touchpoint lain!")
        lines.append("💡 Jika ada perubahan aturan bisnis, update FEATURE-MAP.yaml")

        return "\n".join(lines)

    def run_hook(self, filepath):
        """Jalankan hook check untuk file."""
        relative_path, matched = self.check_file(filepath)
        if matched:
            reminder = self.generate_reminder(relative_path, matched)
            print(reminder)
            return True
        return False

    # ----- pre-commit -----

    def pre_commit_check(self):
        """Pre-commit check - blocks if pending drift."""
        flows = self.parse_feature_map()

        if not flows:
            return True

        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True, timeout=10
            )
            staged = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        except Exception:
            return True

        if not staged:
            return True

        # Cross-role warnings (non-blocking)
        for name, flow in flows.items():
            touchpoints = flow.get('touchpoints', [])
            if len(touchpoints) < 2:
                continue
            touched = set()
            for tp in touchpoints:
                for f in staged:
                    if self.match_touchpoint(f, tp):
                        touched.add(tp)
            if touched:
                untouched = [tp for tp in touchpoints if tp not in touched]
                if untouched:
                    print(f"[feature-map] ⚠️  Warning: Flow '{name}' berubah di touchpoint "
                          f"tapi lainnya tidak ikut")

        # Pending drift (blocking)
        pending_dir = os.path.join(self.project_root, '.freebuff', 'feature-map-pending')
        if os.path.exists(pending_dir):
            pending_flows = []
            for filename in os.listdir(pending_dir):
                if filename.endswith('.json'):
                    flow_id = filename[:-5]
                    pending_flows.append(flow_id)

            if pending_flows:
                staged_flows = self.match_flows(flows, staged)
                blocking = [f for f in pending_flows if f in staged_flows]

                if blocking and os.environ.get('FEATURE_MAP_ACK') != '1':
                    print(f"\n[feature-map] ❌ Commit diblokir!")
                    print(f"[feature-map] {len(blocking)} flow punya drift belum disinkronkan:")
                    for f in blocking:
                        print(f"  - {f}")
                    print(f"\n[feature-map] Solusi:")
                    print(f"  1. Jalankan: python3 freebuff/freebuff_adapter.py sync-apply")
                    print(f"  2. Atau override: FEATURE_MAP_ACK=1 git commit ...")
                    return False

        return True

    # ----- audit -----

    def flow_audit(self, flow_name=None):
        """Audit flow. Returns True if ok, False if error."""
        flows = self.parse_feature_map()

        if not flows:
            print("❌ Tidak ada FEATURE-MAP.yaml atau tidak ada flow")
            return False

        if flow_name:
            if flow_name not in flows:
                print(f"❌ Flow '{flow_name}' tidak ditemukan")
                return False
            flows_to_audit = {flow_name: flows[flow_name]}
        else:
            flows_to_audit = flows

        print("🔍 Feature Map Audit")
        print("=" * 50)

        for name, data in flows_to_audit.items():
            print(f"\n📋 Flow: {name}")
            print(f"   Confidence: {data['confidence']}")
            if data['policy']:
                print(f"   Policy: {data['policy']}")

            missing = []
            for tp in data['touchpoints']:
                matches = globmod.glob(os.path.join(self.project_root, tp))
                if not matches:
                    missing.append(tp)

            if missing:
                print(f"   ⚠️  Touchpoints tidak ditemukan:")
                for m in missing:
                    print(f"      - {m}")
            else:
                print(f"   ✅ Semua touchpoints ada")

            print(f"   📝 Invariants: {len(data['invariants'])}")

        print("\n" + "=" * 50)
        print("Audit selesai!")
        return True

    # ----- status -----

    def flow_sync_status(self):
        """Tampilkan status sync."""
        flows = self.parse_feature_map()

        if not flows:
            print("❌ Tidak ada FEATURE-MAP.yaml")
            return

        print("📊 Feature Map Sync Status")
        print("=" * 50)

        for name, data in flows.items():
            status = "✅" if data['confidence'] in ['reviewed', 'approved'] else "⚠️"
            print(f"{status} {name}: {data['confidence']}")

        print("=" * 50)

    # ----- sync-apply (MVP: list only, manual apply) -----

    def flow_sync_apply(self):
        """Tampilkan pending drift dan instruksi sync manual.

        MVP: Belum melakukan apply/clear otomatis.
        User perlu update FEATURE-MAP.yaml secara manual lalu
        hapus file pending secara manual.
        """
        pending_dir = os.path.join(self.project_root, '.freebuff', 'feature-map-pending')
        pending_files = sorted(globmod.glob(os.path.join(pending_dir, '*.json')))

        if not pending_files:
            print("✅ Tidak ada pending drift Freebuff.")
            return True

        print("⚠️  Pending drift ditemukan:")
        for pending in pending_files:
            print(f"  - {Path(pending).stem}")
        print("")
        print("📋 Langkah manual:")
        print("  1. Baca file pending untuk lihat detail drift")
        print("  2. Update invariant/policy di FEATURE-MAP.yaml")
        print("  3. Hapus file pending yang sudah disinkronkan:")
        print(f"     rm {pending_dir}/<flow-name>.json")
        return False

    # ----- init -----

    def flow_map_init(self):
        """Buat FEATURE-MAP.yaml minimal jika belum ada."""
        if os.path.exists(self.feature_map_path):
            print(f"✅ FEATURE-MAP.yaml sudah ada: {self.feature_map_path}")
            return True

        template = """# Feature Map - Registry Flow Bisnis

flows:
  sample-flow:
    description: "Ganti dengan flow bisnis utama project ini"
    confidence: draft
    policy: "Setiap perubahan touchpoint harus konsisten lintas layer"
    business_aspects:
      - validation
    touchpoints:
      - path: "app/**/*.py"
        role: backend-service
        note: "Ganti dengan path project"
    invariants:
      - "Tulis aturan bisnis yang wajib konsisten"
"""
        with open(self.feature_map_path, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"✅ FEATURE-MAP.yaml dibuat: {self.feature_map_path}")
        return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Main entry point."""
    adapter = FreebuffFeatureMapAdapter()

    if len(sys.argv) < 2:
        print("Usage: freebuff_adapter.py <command> [args]")
        print("")
        print("Commands:")
        print("  hook <file>        - Run hook check for file")
        print("  audit [flow]       - Audit flow(s)")
        print("  status             - Show sync status")
        print("  sync-apply         - Show pending drift (manual apply)")
        print("  init               - Create FEATURE-MAP.yaml if not exists")
        print("  pre-commit         - Run pre-commit check")
        sys.exit(2)

    command = sys.argv[1]

    if command == 'hook':
        if len(sys.argv) < 3:
            print("Error: hook requires a file argument")
            print("Usage: freebuff_adapter.py hook <file>")
            sys.exit(2)
        sys.exit(0 if adapter.run_hook(sys.argv[2]) else 0)

    elif command == 'audit':
        flow = sys.argv[2] if len(sys.argv) > 2 else None
        sys.exit(0 if adapter.flow_audit(flow) else 1)

    elif command == 'status':
        adapter.flow_sync_status()
        sys.exit(0)

    elif command == 'sync-apply':
        sys.exit(0 if adapter.flow_sync_apply() else 1)

    elif command == 'init':
        sys.exit(0 if adapter.flow_map_init() else 1)

    elif command == 'pre-commit':
        sys.exit(0 if adapter.pre_commit_check() else 1)

    else:
        print(f"Error: unknown command '{command}'")
        sys.exit(2)


if __name__ == '__main__':
    main()
