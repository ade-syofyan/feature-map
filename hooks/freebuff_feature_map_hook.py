#!/usr/bin/env python3
"""
Freebuff-compatible PostToolUse hook for feature-map.
Dipanggil oleh Freebuff menggunakan run_file_change_hooks.
"""
import os
import sys
import json
import glob as globmod

def find_feature_map_root():
    """Cari root project yang punya FEATURE-MAP.yaml"""
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'FEATURE-MAP.yaml')):
            return current
        current = os.path.dirname(current)
    return None

def parse_feature_map(filepath):
    """Parse FEATURE-MAP.yaml tanpa PyYAML"""
    flows = {}
    current_flow = None
    in_touchpoints = False
    in_invariants = False
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.rstrip()
            
            # Flow definition
            if line.startswith('  ') and not line.startswith('    ') and ':' in line and not line.strip().startswith('#'):
                flow_name = line.strip().rstrip(':').strip()
                if flow_name and not flow_name.startswith('-'):
                    current_flow = flow_name
                    flows[current_flow] = {
                        'touchpoints': [],
                        'invariants': [],
                        'policy': '',
                        'business_aspects': []
                    }
                    in_touchpoints = False
                    in_invariants = False
            
            # Touchpoints section
            if 'touchpoints:' in line and current_flow:
                in_touchpoints = True
                in_invariants = False
                continue
            
            # Invariants section
            if 'invariants:' in line and current_flow:
                in_invariants = True
                in_touchpoints = False
                continue
            
            # Policy
            if 'policy:' in line and current_flow:
                policy = line.split('policy:', 1)[1].strip().strip('"').strip("'")
                flows[current_flow]['policy'] = policy
                in_touchpoints = False
                in_invariants = False
            
            # Touchpoint path
            if in_touchpoints and 'path:' in line:
                path = line.split('path:', 1)[1].strip().strip('"').strip("'")
                flows[current_flow]['touchpoints'].append(path)
            
            # Invariant
            if in_invariants and line.strip().startswith('- '):
                invariant = line.strip()[2:].strip().strip('"').strip("'")
                flows[current_flow]['invariants'].append(invariant)
    
    return flows

def match_touchpoint(filepath, pattern):
    """Simple glob matching"""
    import fnmatch
    return fnmatch.fnmatch(filepath, pattern)

def check_edited_file(filepath):
    """Cek apakah file yang diedit adalah touchpoint"""
    root = find_feature_map_root()
    if not root:
        return None, []
    
    feature_map_path = os.path.join(root, 'FEATURE-MAP.yaml')
    if not os.path.exists(feature_map_path):
        return None, []
    
    flows = parse_feature_map(feature_map_path)
    relative_path = os.path.relpath(filepath, root)
    
    matched_flows = []
    for flow_name, flow_data in flows.items():
        for touchpoint in flow_data['touchpoints']:
            if match_touchpoint(relative_path, touchpoint):
                matched_flows.append({
                    'name': flow_name,
                    'touchpoints': flow_data['touchpoints'],
                    'invariants': flow_data['invariants'],
                    'policy': flow_data['policy']
                })
    
    return relative_path, matched_flows

def generate_reminder(filepath, matched_flows):
    """Generate reminder message"""
    if not matched_flows:
        return None
    
    lines = ["[feature-map] File yang baru diedit adalah touchpoint:"]
    lines.append(f"  File: {filepath}")
    
    for flow in matched_flows:
        lines.append(f"\n  Flow: {flow['name']}")
        if flow['policy']:
            lines.append(f"  Policy: {flow['policy']}")
        
        lines.append("  Touchpoint lain:")
        for tp in flow['touchpoints']:
            lines.append(f"    - {tp}")
        
        if flow['invariants']:
            lines.append("  Invariants:")
            for inv in flow['invariants']:
                lines.append(f"    - {inv}")
    
    lines.append("\n  Pastikan perubahan Anda konsisten dengan touchpoint lain!")
    lines.append("  Jika ada perubahan aturan bisnis, update FEATURE-MAP.yaml.")
    
    return "\n".join(lines)

def main():
    """Main hook function"""
    # Get file from environment or arguments
    filepath = os.environ.get('FREEBUFF_CHANGED_FILE', '')
    if not filepath and len(sys.argv) > 1:
        filepath = sys.argv[1]
    
    if not filepath:
        return
    
    # Check if file is a touchpoint
    relative_path, matched_flows = check_edited_file(filepath)
    
    if matched_flows:
        reminder = generate_reminder(relative_path, matched_flows)
        print(reminder)

if __name__ == '__main__':
    main()
