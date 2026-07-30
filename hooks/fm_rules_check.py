#!/usr/bin/env python3
"""Cross-check a flow's declared invariants against its test touchpoints.

Regression tests often encode exact business rules ("office is excluded
from the empty-NRP warning") as human-readable descriptions before anyone
writes them into FEATURE-MAP.yaml. This script extracts those descriptions
from test touchpoints and flags ones whose content words barely overlap
with the flow's declared policy/invariants text — a signal that a rule
exists in code and tests but was never written into the registry.

Heuristic, not authoritative: a flagged test may already be covered by an
invariant phrased differently. Findings are for human review, not
auto-writing.

CLI: python3 fm_rules_check.py <repo_root> <flow_name>  -> JSON report.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_map_hook import find_feature_map, match, parse_feature_map

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "not", "no", "when", "for", "on", "of", "to",
    "from", "with", "and", "or", "but", "this", "that", "it", "its",
    "into", "even", "still", "has", "have", "had", "in", "at", "as",
    "by", "if", "than", "then", "so", "each", "any", "all", "can",
    "should", "must", "also", "only", "still", "test", "tests", "row",
    "rows", "returns", "return", "value", "values", "correctly",
    "properly", "case", "cases", "example", "examples", "given",
}

PEST_RE = re.compile(
    r"""\b(?:it|test)\s*\(\s*(['"])(.+?)\1\s*,""", re.IGNORECASE | re.DOTALL
)
PHPUNIT_METHOD_RE = re.compile(r"function\s+test_?([A-Za-z0-9_]+)\s*\(")


def _words_from_camel_snake(name):
    name = name.replace("_", " ")
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    return name.lower()


def extract_test_descriptions(text):
    """Return a list of human-readable test descriptions found in a file."""
    descriptions = []
    for m in PEST_RE.finditer(text):
        desc = re.sub(r"\s+", " ", m.group(2)).strip()
        if desc:
            descriptions.append(desc)
    for m in PHPUNIT_METHOD_RE.finditer(text):
        desc = _words_from_camel_snake(m.group(1)).strip()
        if desc:
            descriptions.append(desc)
    return descriptions


def significant_words(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]*", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def is_test_touchpoint(path):
    lowered = path.lower()
    return (
        "test" in lowered.split("/")
        or lowered.endswith("test.php")
        or "_test.py" in lowered
        or lowered.endswith(".spec.ts")
        or lowered.endswith(".spec.js")
        or "/tests/" in lowered
    )


def find_files(root, glob_path):
    matches = []
    for dirpath, _dirnames, filenames in os.walk(root):
        if "/.git" in dirpath or "/node_modules" in dirpath or "/vendor" in dirpath:
            continue
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root)
            if match(rel, glob_path):
                matches.append(rel)
    return matches


def check_flow(root, flow_name, flow):
    invariant_text = " ".join(flow.get("invariants", [])) + " " + flow.get("policy", "")
    invariant_words = significant_words(invariant_text)

    findings = []
    checked_files = []
    for tp in flow.get("touchpoints", []):
        path = tp.get("path", "")
        if not path or "repo" in tp:
            continue
        if not is_test_touchpoint(path):
            continue
        for rel in find_files(root, path):
            full = os.path.join(root, rel)
            try:
                with open(full, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            checked_files.append(rel)
            for desc in extract_test_descriptions(text):
                desc_words = significant_words(desc)
                if not desc_words:
                    continue
                overlap = desc_words & invariant_words
                coverage = len(overlap) / len(desc_words)
                if coverage < 0.4:
                    findings.append({
                        "file": rel,
                        "test_description": desc,
                        "coverage": round(coverage, 2),
                        "unmatched_terms": sorted(desc_words - overlap),
                    })

    return {
        "flow": flow_name,
        "checked_test_files": checked_files,
        "possible_undocumented_rules": findings,
    }


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: fm_rules_check.py <repo_root> <flow_name>"}))
        return
    root = os.path.abspath(sys.argv[1])
    flow_name = sys.argv[2]

    fm_path = find_feature_map(root)
    if not fm_path:
        print(json.dumps({"error": "FEATURE-MAP.yaml not found"}))
        return
    with open(fm_path, encoding="utf-8") as f:
        flows = parse_feature_map(f.read())

    if flow_name not in flows:
        print(json.dumps({"error": f"flow '{flow_name}' not found",
                           "available_flows": sorted(flows.keys())}))
        return

    result = check_flow(os.path.dirname(fm_path), flow_name, flows[flow_name])
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
