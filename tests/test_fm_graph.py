import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import fm_graph


def make_graph(tmp_path):
    d = tmp_path / ".code-review-graph"
    d.mkdir()
    con = sqlite3.connect(str(d / "graph.db"))
    con.executescript("""
        CREATE TABLE nodes (qualified_name TEXT, file_path TEXT);
        CREATE TABLE edges (kind TEXT, source_qualified TEXT,
                            target_qualified TEXT, file_path TEXT, line INTEGER);
        INSERT INTO nodes VALUES ('hr.lembur.calc', 'hr/lembur/calc.py');
        INSERT INTO nodes VALUES ('hr.approval.approve', 'hr/approval/svc.py');
        INSERT INTO edges VALUES ('CALLS', 'hr.approval.approve',
                                  'hr.lembur.calc', 'hr/approval/svc.py', 120);
        INSERT INTO edges VALUES ('IMPORTS_FROM', 'x', 'hr.lembur.calc', 'y.py', 1);
    """)
    con.commit(); con.close()
    return str(tmp_path)


def test_callers_of_files_finds_calls_only(tmp_path):
    root = make_graph(tmp_path)
    result = fm_graph.callers_of_files(root, ["hr/lembur/calc.py", "via:lembur"])
    assert result == {"hr/lembur/calc.py": [
        {"caller": "hr.approval.approve", "file": "hr/approval/svc.py", "line": 120}]}


def test_missing_db_returns_empty(tmp_path):
    assert fm_graph.graph_available(str(tmp_path)) is False
    assert fm_graph.callers_of_files(str(tmp_path), ["a.py"]) == {}


def test_corrupt_db_returns_empty(tmp_path):
    d = tmp_path / ".code-review-graph"
    d.mkdir()
    (d / "graph.db").write_text("bukan sqlite")
    assert fm_graph.callers_of_files(str(tmp_path), ["a.py"]) == {}
