#!/usr/bin/env python3
"""
Freebuff Adapter for feature-map plugin.
Menyediakan hook dan command yang kompatibel dengan Freebuff.
"""
import os
import sys
import json
import glob as globmod
import subprocess
from pathlib import Path

class FreebuffFeatureMapAdapter:
    """Adapter untuk menjalankan feature-map di Freebuff"""
    
    def __init__(self, project_root=None):
        self.project_root = project_root or os.getcwd()
        self.feature_map_path = os.path.join(self.project_root, 'FEATURE-MAP.yaml')
        
    def parse_feature_map(self):
        """Parse FEATURE-MAP.yaml tanpa PyYAML"""
        if not os.path.exists(self.feature_map_path):
            return {}
            
        flows = {}
        current_flow = None
        current_section = None
        
        with open(self.feature_map_path, 'r') as f:
            for line in f:
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
                    if stripped.strip() == 'touchpoints:':
                        current_section = 'touchpoints'
                        continue
                    elif stripped.strip() == 'invariants:':
                        current_section = 'invariants'
                        continue
                    elif stripped.strip() == 'business_aspects:':
                        current_section = 'business_aspects'
                        continue
                    elif stripped.strip() == 'history:':
                        current_section = 'history'
                        continue
                    elif 'policy:' in stripped:
                        policy = stripped.split('policy:', 1)[1].strip().strip('"').strip("'")
                        flows[current_flow]['policy'] = policy
                        current_section = None
                        continue
                    elif 'confidence:' in stripped:
                        conf = stripped.split('confidence:', 1)[1].strip()
                        flows[current_flow]['confidence'] = conf
                        current_section = None
                        continue
                    elif 'mechanics_doc:' in stripped:
                        current_section = None
                        continue
                    elif 'description:' in stripped:
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
                # Skip history section items
                elif current_section == 'history':
                    continue
        
        return flows
    
    def match_touchpoint(self, filepath, pattern):
        """Simple glob matching"""
        import fnmatch
        return fnmatch.fnmatch(filepath, pattern)
    
    def match_flows(self, flows, files):
        """Find flows that match given files"""
        matched = set()
        for flow_name, flow_data in flows.items():
            for tp in flow_data['touchpoints']:
                for f in files:
                    if self.match_touchpoint(f, tp):
                        matched.add(flow_name)
        return matched
    
    def check_file(self, filepath):
        """Cek apakah file adalah touchpoint"""
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
        """Generate reminder untuk Freebuff"""
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
        """Jalankan hook check untuk file"""
        relative_path, matched = self.check_file(filepath)
        if matched:
            reminder = self.generate_reminder(relative_path, matched)
            print(reminder)
            return True
        return False
    
    def pre_commit_check(self):
        """Pre-commit check - blocks if pending drift"""
        flows = self.parse_feature_map()
        
        if not flows:
            return True  # No FEATURE-MAP.yaml, allow commit
        
        # Get staged files
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True, timeout=10
            )
            staged = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        except Exception:
            return True  # Can't get staged files, allow commit
        
        if not staged:
            return True  # No staged files, allow commit
        
        # Check cross-role warnings (non-blocking)
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
        
        # Check pending drift (blocking)
        pending_dir = os.path.join(self.project_root, '.freebuff', 'feature-map-pending')
        if os.path.exists(pending_dir):
            pending_flows = []
            for filename in os.listdir(pending_dir):
                if filename.endswith('.json'):
                    flow_id = filename[:-5]  # Remove .json
                    pending_flows.append(flow_id)
            
            if pending_flows:
                # Check if any pending flow is affected by staged files
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
    
    def flow_audit(self, flow_name=None):
        """Audit flow"""
        flows = self.parse_feature_map()
        
        if not flows:
            print("❌ Tidak ada FEATURE-MAP.yaml atau tidak ada flow")
            return
        
        if flow_name:
            if flow_name not in flows:
                print(f"❌ Flow '{flow_name}' tidak ditemukan")
                return
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
            
            # Check touchpoints exist
            missing = []
            for tp in data['touchpoints']:
                import glob
                matches = glob.glob(os.path.join(self.project_root, tp))
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
    
    def flow_sync_status(self):
        """Tampilkan status sync"""
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

    def flow_sync_apply(self):
        """Tampilkan pending drift dan instruksi sync manual."""
        pending_dir = os.path.join(self.project_root, '.freebuff', 'feature-map-pending')
        pending_files = sorted(globmod.glob(os.path.join(pending_dir, '*.json')))

        if not pending_files:
            print("✅ Tidak ada pending drift Freebuff.")
            return True

        print("⚠️  Pending drift ditemukan:")
        for pending in pending_files:
            print(f"  - {Path(pending).stem}")
        print("")
        print("Review pending file, update FEATURE-MAP.yaml bila perlu, lalu clear file pending yang sudah disinkronkan.")
        return False

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


def main():
    """Main entry point"""
    adapter = FreebuffFeatureMapAdapter()
    
    if len(sys.argv) < 2:
        print("Usage: freebuff_adapter.py <command> [args]")
        print("Commands:")
        print("  hook <file>        - Run hook check for file")
        print("  audit [flow]       - Audit flow(s)")
        print("  status             - Show sync status")
        print("  pre-commit         - Run pre-commit check")
        return
    
    command = sys.argv[1]
    
    if command == 'hook':
        if len(sys.argv) < 3:
            print("Usage: freebuff_adapter.py hook <file>")
            return
        adapter.run_hook(sys.argv[2])
    
    elif command == 'audit':
        flow = sys.argv[2] if len(sys.argv) > 2 else None
        adapter.flow_audit(flow)
    
    elif command == 'status':
        adapter.flow_sync_status()

    elif command == 'sync-apply':
        if adapter.flow_sync_apply():
            sys.exit(0)
        else:
            sys.exit(1)

    elif command == 'init':
        if adapter.flow_map_init():
            sys.exit(0)
        else:
            sys.exit(1)

    elif command == 'pre-commit':
        if adapter.pre_commit_check():
            sys.exit(0)
        else:
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()
