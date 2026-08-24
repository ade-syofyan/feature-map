#!/usr/bin/env python3
"""Generate FEATURE-MAP.yaml draft from blueprint/FRD/SRS text or PDF.

The importer is intentionally heuristic. It produces a reviewable draft with
page evidence and generic path placeholders, then humans/agents bind those
placeholders to real code paths during development.
"""

import argparse
import os
import re
import sys


WORKFLOW_RE = re.compile(r"\b(?:\d+\.\s*)?WORKFLOW\s+([A-Z0-9 &/+-]+)")
STOP_RE = re.compile(r"\b(?:\d+\.\s*)?WORKFLOW\s+[A-Z0-9 &/+-]+|\bBAB-[IVXLCDM]+|\bKESIMPULAN\b")


def slugify(text):
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "flow"


def clean_title(text):
    return re.sub(r"\s+", " ", text).strip(" .:-")


def normalize_workflow_title(text):
    text = clean_title(text.split("................................")[0])
    text = re.sub(r"\s+[A-Z]$", "", text)
    text = re.split(
        r"\b(?:Input|Proses|Data|Output|Sistem|Tujuan|Pemicu|Status)\b",
        text,
        maxsplit=1,
    )[0]
    return clean_title(text)


def yaml_quote(text):
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def read_pages(path):
    if not os.path.exists(path):
        raise SystemExit(f"Document not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise SystemExit(
                "PDF import needs pypdf. Install it with: python3 -m pip install pypdf"
            ) from exc
        reader = PdfReader(path)
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]

    with open(path, encoding="utf-8") as f:
        return [(1, f.read())]


def section_snippet(text, start):
    end = len(text)
    for match in STOP_RE.finditer(text, start + 8):
        end = match.start()
        break
    snippet = re.sub(r"\s+", " ", text[start:end]).strip()
    return snippet[:900]


def extract_terms(snippet):
    terms = []
    patterns = [
        r"Status:\s*([^\.]+)",
        r"Data:\s*([^\.]+)",
        r"Input:\s*([^\.]+)",
        r"Output:\s*([^\.]+)",
        r"Sistem:\s*([^\.]+)",
    ]
    for pattern in patterns:
        found = re.search(pattern, snippet, flags=re.IGNORECASE)
        if found:
            val = clean_title(found.group(1))
            if val and val not in terms:
                terms.append(val)
    return terms[:3]


def infer_paths(slug):
    parts = [p for p in slug.split("-") if p not in ("workflow", "modul")]
    key = parts[0] if parts else slug
    return [
        (f"app/**/{key}/**", "backend-service", "Placeholder backend/service path; bind to real files during development"),
        (f"resources/**/{key}/**", "admin-view", "Placeholder UI/admin path; bind to real files during development"),
        (f"database/migrations/**{key}**", "db-migration", "Placeholder schema path; bind to real migrations during development"),
    ]


def extract_workflows(pages, _source_name=None):
    flows = []
    seen = set()
    for page, text in pages:
        for match in WORKFLOW_RE.finditer(text):
            raw_title = normalize_workflow_title(match.group(1))
            if not raw_title or raw_title in {"SYSTEM", "UTAMA PT"}:
                continue
            if len(raw_title) < 4:
                continue
            if "................................" in text[match.end():match.end() + 30]:
                continue
            slug = slugify(raw_title)
            if slug in seen:
                continue
            seen.add(slug)
            snippet = section_snippet(text, match.start())
            terms = extract_terms(snippet)
            flows.append({
                "slug": slug,
                "title": raw_title.title(),
                "page": page,
                "snippet": snippet,
                "terms": terms,
            })
    return flows


def build_flow_yaml(flow, source_path):
    slug = flow["slug"]
    title = flow["title"]
    lines = [
        f"  {slug}:",
        f"    description: {yaml_quote(title)}",
        "    confidence: draft",
        f"    policy: {yaml_quote('Follow blueprint workflow for ' + title)}",
        "    evidence:",
        f"      - source: {yaml_quote(source_path)}",
        f"        page: {flow['page']}",
        f"        section: {yaml_quote('WORKFLOW ' + title.upper())}",
        "    touchpoints:",
        f"      - path: {yaml_quote(source_path)}",
        "        role: docs",
        f"        note: {yaml_quote('Blueprint evidence page ' + str(flow['page']))}",
    ]
    for path, role, note in infer_paths(slug):
        lines.extend([
            f"      - path: {yaml_quote(path)}",
            f"        role: {role}",
            f"        note: {yaml_quote(note)}",
        ])

    lines.append("    invariants:")
    if flow["terms"]:
        for term in flow["terms"]:
            lines.append(f"      - {yaml_quote(term + ' must stay consistent across docs, UI, backend, database, and reports')}")
    else:
        lines.append(f"      - {yaml_quote(title + ' workflow status and output must stay consistent across docs, UI, backend, database, and reports')}")
    return "\n".join(lines)


def generate_feature_map(path, source_path=None):
    source_path = source_path or path
    pages = read_pages(path)
    flows = extract_workflows(pages, os.path.basename(path))
    lines = [
        "# Generated by feature-map blueprint importer.",
        "# Review before use. Replace placeholder paths with real code paths.",
        "flows:",
    ]
    if not flows:
        lines.extend([
            "  imported-blueprint:",
            "    description: \"Imported blueprint\"",
            "    confidence: draft",
            "    policy: \"Review source document and split into business flows\"",
            "    evidence:",
            f"      - source: {yaml_quote(source_path)}",
            "        page: 1",
            "        section: \"Document\"",
            "    touchpoints:",
            f"      - path: {yaml_quote(source_path)}",
            "        role: docs",
            "    invariants:",
            "      - \"Blueprint requirements must be mapped to implementation touchpoints\"",
        ])
    for flow in flows:
        lines.append(build_flow_yaml(flow, source_path))
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", help="Blueprint/FRD/SRS PDF or text file")
    parser.add_argument("-o", "--output", help="Output YAML path; defaults to stdout")
    parser.add_argument("--source-path", help="Path to store in touchpoint/evidence")
    args = parser.parse_args(argv)

    rendered = generate_feature_map(args.document, args.source_path)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
