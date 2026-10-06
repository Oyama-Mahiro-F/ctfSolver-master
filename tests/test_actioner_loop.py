"""actioner 主循环的收敛性回归测试。

审计发现：`or (vuln == 'OTHER')` 使 OTHER 永不因总结退出、白跑满 30 轮并把
已有结论覆盖成 vuln=False；而 IDOR/LFI 的循环完全没有步数上限。
"""
import pytest


PAGE = {
    "name": "p",
    "request": {"url": "http://example.com/?id=1", "method": "GET"},
    "response": {"status": 200, "content": "ok"},
}


@pytest.fixture
def actioner_env(agent_path, monkeypatch):
    import agents.actioner as actioner
    from config import config

    monkeypatch.setattr(actioner, "add_message", lambda *a, **k: "session-id")
    monkeypatch.setattr(
        actioner.agent_manager, "send_pure_message_with_status", lambda *a, **k: {"id": "msg-1"}
    )
    monkeypatch.setattr(
        actioner.agent_manager, "update_pure_message_status", lambda *a, **k: True
    )
    monkeypatch.setattr(actioner.agent_manager, "current_task_id", "task-1", raising=False)
    config.FLAG = ""
    return actioner, config


def test_other_summary_terminates_and_keeps_conclusion(actioner_env, monkeypatch):
    actioner, config = actioner_env
    config.NEED_FLAG = False
    calls = {"n": 0}

    def fake_chat(prompt, session_id, *a, **k):
        calls["n"] += 1
        return "<summary><vuln>True</vuln><desc>found</desc><needDeep>False</needDeep></summary>"

    monkeypatch.setattr(actioner, "chat", fake_chat)

    result = actioner.execute_solution({"vuln": "OTHER", "desc": "d"}, PAGE, "k", [], [])

    assert calls["n"] <= 5, f"OTHER 类型未及时收敛，调用了 {calls['n']} 次 LLM"
    assert result["summary"]["vuln"] == "True", "已得出的结论被兜底覆盖了"


def test_need_flag_injections_are_capped(actioner_env, monkeypatch):
    actioner, config = actioner_env
    config.NEED_FLAG = True
    calls = {"n": 0}

    def fake_chat(prompt, session_id, *a, **k):
        calls["n"] += 1
        return "<summary><vuln>True</vuln><desc>found</desc></summary>"

    monkeypatch.setattr(actioner, "chat", fake_chat)

    result = actioner.execute_solution({"vuln": "OTHER", "desc": "d"}, PAGE, "k", {}, [])

    assert calls["n"] <= 5, f"深入利用提示未被限次，共 {calls['n']} 轮"
    assert result["summary"]["vuln"] == "True"


def test_non_other_loop_is_bounded(actioner_env, monkeypatch):
    """回归：IDOR/LFI 的 while True 没有步数上限。"""
    actioner, config = actioner_env
    config.NEED_FLAG = False
    calls = {"n": 0}

    def fake_chat(prompt, session_id, *a, **k):
        calls["n"] += 1
        return "这一轮没有给出任何 XML 指令"

    monkeypatch.setattr(actioner, "chat", fake_chat)

    result = actioner.execute_solution({"vuln": "LFI", "desc": "d"}, PAGE, "k", {}, [])

    assert calls["n"] == 30, f"循环未被 max_steps 截断，共 {calls['n']} 轮"
    assert result["summary"]["vuln"] == "False"


def test_plain_text_summary_is_normalized(actioner_env, monkeypatch):
    """回归：<summary>纯文本</summary> 返回 str，调用方 .get 会 AttributeError。"""
    actioner, config = actioner_env
    config.NEED_FLAG = False

    monkeypatch.setattr(
        actioner, "chat", lambda *a, **k: "<summary>这是一段纯文本总结</summary>"
    )

    result = actioner.execute_solution({"vuln": "OTHER", "desc": "d"}, PAGE, "k", [], [])

    assert isinstance(result["summary"], dict)
    assert result["summary"]["vuln"] == "False"
