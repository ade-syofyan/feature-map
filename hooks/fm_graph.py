#!/usr/bin/env python3
"""Baca call-graph code-review-graph (.code-review-graph/graph.db) read-only.

Opsional penuh: DB tidak ada / korup / skema beda -> hasil kosong, tanpa
exception. Dipakai /flow-audit untuk blast radius per-fungsi.

CLI: python3 fm_graph.py <root> <rel_path...>  -> JSON callers_of_files.
"""
import json
import os
import sqlite3
import sys


def _db_path(root):
    return os.path.join(root, ".code-review-graph", "graph.db")


def graph_available(root):
    return os.path.isfile(_db_path(root))


def callers_of_files(root, rel_paths):
    if not graph_available(root):
        return {}
    try:
        con = sqlite3.connect(f"file:{_db_path(root)}?mode=ro", uri=True,
                              timeout=2)
        cur = con.cursor()
        result = {}
        for rel in rel_paths:
            if rel.startswith("via:"):
                continue
            rows = cur.execute(
                "SELECT DISTINCT e.source_qualified, e.file_path, e.line "
                "FROM edges e JOIN nodes n "
                "ON n.qualified_name = e.target_qualified "
                "WHERE e.kind = 'CALLS' AND n.file_path = ?", (rel,)).fetchall()
            callers = [{"caller": r[0], "file": r[1], "line": r[2]}
                       for r in rows]
            if callers:
                result[rel] = callers
        con.close()
        return result
    except Exception:
        return {}


def main():
    if len(sys.argv) < 3:
        print("{}")
        return
    print(json.dumps(callers_of_files(sys.argv[1], sys.argv[2:]), indent=2))


if __name__ == "__main__":
    main()
