"""agent 端工具函数回归测试（使用临时数据库，不触碰仓库自带 chat.db）。"""
import json
import os
import sqlite3

import pytest


@pytest.fixture
def temp_agent_db(agent_path, monkeypatch, repo_tmpdir):
    """把 sql_helper 指向一个临时库，并按 init.sql 建表。"""
    from config import config
    from utils import sql_helper

    db_path = os.path.join(repo_tmpdir, "chat.db")
    monkeypatch.setattr(sql_helper, "DB_PATH", db_path)

    conn = sqlite3.connect(db_path)
    with open(config.INIT_SQL, "r", encoding="utf-8") as f:
        for statement in f.read().split(";"):
            if statement.strip():
                conn.execute(statement)
    conn.commit()
    conn.close()
    return db_path


def test_sql_helper_roundtrip(temp_agent_db):
    from utils.sql_helper import SQLiteHelper

    assert SQLiteHelper.insert_record("sessions", {"session_id": "s1", "parent_id": None}) is True
    rows = SQLiteHelper.select_records("sessions", condition={"session_id": "s1"})
    assert len(rows) == 1
    assert SQLiteHelper.fetch_one("SELECT session_id FROM sessions WHERE session_id = ?", ("s1",)) == ("s1",)


def test_task_helper_tolerates_null_request_json(temp_agent_db):
    """回归：request_json 为 NULL 时 json.loads 抛 TypeError，会中断整条扫描。"""
    from utils import task_helper
    from utils.sql_helper import SQLiteHelper

    SQLiteHelper.insert_record("vulns", {
        "id": "v1", "task_id": "t1", "vuln_type": "XSS", "desc": "d", "request_json": None,
    })
    vulns = task_helper.get_all_vulns("t1")
    assert len(vulns) == 1
    assert vulns[0]["request_json"] == {}


def test_page_helper_missing_file_returns_empty(temp_agent_db):
    """回归：parent_path 不存在/为 NULL 时 open() 抛异常打断探索。"""
    from utils import page_helper

    assert page_helper.get_parent_page("does-not-exist") == {}

    page_helper.insert_page_parent("/tmp/definitely-missing-page.json", "page-1")
    assert page_helper.get_parent_page("page-1") == {}


def test_page_helper_reads_existing_parent(temp_agent_db, tmp_path):
    from utils import page_helper

    parent_file = tmp_path / "parent.json"
    parent_file.write_text(json.dumps({"name": "parent"}), encoding="utf-8")
    page_helper.insert_page_parent(str(parent_file), "page-2")
    assert page_helper.get_parent_page("page-2") == {"name": "parent"}


def test_saver_fallback_on_bad_llm_output(agent_path, monkeypatch):
    """回归：模型不给 <result> 时 IndexError 会打断页面探索。"""
    from agents import saver

    monkeypatch.setattr(saver, "add_message", lambda *a, **k: "sid")
    monkeypatch.setattr(saver, "chat", lambda *a, **k: "完全没有 XML 的输出")

    result = saver.save_page({"request": {}, "response": {}})
    assert result["name"]
    assert "key" in result
    assert "flag" in result


def test_saver_merges_missing_fields(agent_path, monkeypatch):
    from agents import saver

    monkeypatch.setattr(saver, "add_message", lambda *a, **k: "sid")
    monkeypatch.setattr(saver, "chat", lambda *a, **k: "<result><name>only-name</name></result>")

    result = saver.save_page({"request": {}, "response": {}})
    assert result["name"] == "only-name"
    assert result["key"] == ""
    assert result["flag"] == ""


def test_run_shell_accepts_documented_code_key(agent_path):
    """回归：文档写的是 <code>，代码却读 params['command']，导致该工具不可用。"""
    from addons import run_shell

    out = run_shell.run({"code": "echo documented-key-works"})
    assert "documented-key-works" in out


def test_run_python_accepts_bare_string(agent_path):
    from addons import run_python

    out = run_python.run("print('py-ok')")
    assert "py-ok" in out
