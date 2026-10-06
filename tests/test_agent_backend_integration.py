"""端到端联调：让 agent 端真实的 AgentManager 通过 HTTP 与 Flask 后端对话。

这覆盖了主链路的协议面：注册 → 心跳 → 领取任务 → 上报页面/漏洞/消息 → 提交 flag。
"""
import json
import threading

import pytest


@pytest.fixture
def live_backend(backend_client):
    """复用已初始化的 app，另起一个真实 HTTP 端口供 requests 访问。"""
    from werkzeug.serving import make_server

    import app as backend_app

    server = make_server("127.0.0.1", 0, backend_app.app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def test_agent_manager_full_protocol(agent_path, live_backend):
    import requests

    from config import config

    config.SERVER_URL = live_backend
    config.NAME = "smoke-agent"
    config.API_MODEL_ACTION = "deepseek-chat"

    from utils.agent_manager import AgentManager

    manager = AgentManager()
    assert manager.register_agent() is True
    assert manager.agent_id

    try:
        assert manager.send_heartbeat() is True

        created = requests.post(
            f"{live_backend}/api/tasks",
            json={"target": "http://example.com", "description": "smoke", "agent_id": manager.agent_id},
            timeout=10,
        ).json()
        task_id = created["data"]["id"]
        manager.current_task_id = task_id

        # agent 通过轮询领取分配给自己的 pending 任务
        pending = manager.get_assigned_tasks()
        assert any(t["id"] == task_id for t in pending), pending

        assert manager.update_task_status(task_id, status="running") is True

        # 页面/漏洞上报返回的对象里 request/response 必须是对象而不是被双重编码的字符串
        page = manager.create_page(task_id, {
            "name": "p",
            "request": json.dumps({"url": "http://example.com", "method": "GET"}),
            "response": json.dumps({"status": 200, "content": "ok"}),
            "description": "d",
            "key": "k",
        })
        assert page is not None
        assert isinstance(page["request"], dict)
        assert page["request"]["url"] == "http://example.com"

        vuln = manager.create_vulnerability(task_id, {
            "vuln_type": "LFI",
            "description": "d",
            "request": json.dumps({"url": "http://example.com"}),
            "response": json.dumps({"status": 200}),
        })
        assert vuln is not None

        message = manager.send_pure_message_with_status(task_id, "hello", "running")
        assert message and message.get("id")
        assert manager.update_pure_message_status(message["id"], "finish", "done") is True

        assert manager.send_summary_message(task_id, {"vuln": True, "findFlag": False}) is not None
        assert manager.send_page_message(task_id, [{"page_id": "p1"}]) is not None
        assert manager.send_vulnerability_message(task_id, [{"id": vuln["id"]}]) is not None

        assert manager.create_flag(task_id, "flag{smoke}") is not None
        assert manager.update_task_status(task_id, status="finished", flag="flag{smoke}") is True

        final = requests.get(f"{live_backend}/api/tasks/{task_id}", timeout=10).json()["data"]
        assert final["status"] == "finished"
        assert final["flag"] == "flag{smoke}"
    finally:
        manager.unregister_agent()
