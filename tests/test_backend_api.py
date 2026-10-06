"""后端 API 回归测试。

覆盖审计中发现并修复的后端缺陷：models.to_dict 崩溃、task_path 脏数据打挂列表、
get_json 415/400 被吞成 500、Agent 在线统计、task 删除级联、toggle 状态同步、
request/response 双重编码、message 双过滤等。
"""
import uuid


def _make_agent(client, status="idle"):
    resp = client.post("/api/agents/register", json={
        "name": f"agent-{uuid.uuid4().hex[:6]}",
        "host": "localhost",
        "port": 0,
        "status": status,
        "capabilities": ["web_scan"],
        "metadata": {"start_time": "2025-01-01T00:00:00"},
    })
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return resp.get_json()["data"]


def _make_task(client, agent_id=None, **extra):
    payload = {"target": "http://example.com", "description": "desc", "agent_id": agent_id}
    payload.update(extra)
    resp = client.post("/api/tasks", json=payload)
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return resp.get_json()["data"]


def test_health_and_root(backend_client):
    assert backend_client.get("/health").status_code == 200
    assert backend_client.get("/").status_code == 200


def test_register_and_list_agents(backend_client):
    agent = _make_agent(backend_client)
    resp = backend_client.get("/api/agents")
    assert resp.status_code == 200
    assert any(a["id"] == agent["id"] for a in resp.get_json()["data"])


def test_agent_status_counts_business_states_as_online(backend_client):
    """回归：agent 端上报 idle/running，原实现只认 'online'，导致在线数恒为 0。"""
    _make_agent(backend_client, status="idle")
    resp = backend_client.get("/api/agents/status")
    assert resp.status_code == 200
    stats = resp.get_json()["data"]["statistics"]
    assert stats["total_agents"] >= 1
    assert stats["online_agents"] == stats["total_agents"] - stats["offline_agents"]
    assert stats["online_agents"] >= 1


def test_register_agent_bad_start_time_does_not_500(backend_client):
    """回归：非法 start_time 曾导致 500。"""
    resp = backend_client.post("/api/agents/register", json={
        "name": "bad-time-agent",
        "host": "localhost",
        "port": 0,
        "start_time": "not-a-date",
    })
    assert resp.status_code == 201, resp.get_data(as_text=True)


def test_task_crud_exposes_task_path(backend_client):
    """回归：Task.to_dict 曾漏掉 task_path，前端拿到 undefined。"""
    task = _make_task(backend_client, task_path="/tmp/whatever")
    resp = backend_client.get(f"/api/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["task_path"] == "/tmp/whatever"


def test_task_list_survives_bad_task_path(backend_client):
    """回归：task_path 指向普通文件时 os.listdir 抛 NotADirectoryError，列表整体 500。"""
    _make_task(backend_client, task_path="/etc/hostname")
    resp = backend_client.get("/api/tasks")
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert resp.get_json()["success"] is True


def test_invalid_json_body_returns_400_not_500(backend_client):
    """回归：Flask 的 415/400 曾被 except Exception 统一转成 500。"""
    resp = backend_client.post("/api/tasks", data="{oops", content_type="application/json")
    assert resp.status_code == 400, resp.get_data(as_text=True)
    resp2 = backend_client.post("/api/tasks")
    assert resp2.status_code == 400, resp2.get_data(as_text=True)


def test_pages_accept_json_string_request(backend_client):
    """回归：agent 端传的是 json.dumps(...) 字符串，曾被双重编码成字符串返回。"""
    task = _make_task(backend_client)
    resp = backend_client.post("/api/pages", json={
        "name": "page1",
        "task_id": task["id"],
        "request": '{"url": "http://example.com", "method": "GET"}',
        "response": '{"status": 200, "content": "ok"}',
        "description": "d",
        "key": "k",
    })
    assert resp.status_code == 201, resp.get_data(as_text=True)
    data = resp.get_json()["data"]
    assert isinstance(data["request"], dict), data["request"]
    assert data["request"]["url"] == "http://example.com"

    listed = backend_client.get("/api/pages")
    assert listed.status_code == 200, listed.get_data(as_text=True)
    assert isinstance(listed.get_json()["data"][0]["request"], dict)


def test_vulns_accept_dict_and_json_string(backend_client):
    task = _make_task(backend_client)
    resp = backend_client.post("/api/vulns", json={
        "vuln_type": "LFI",
        "task_id": task["id"],
        "request": {"url": "http://example.com?f=1"},
        "response": '{"status": 200}',
        "description": "d",
    })
    assert resp.status_code == 201, resp.get_data(as_text=True)
    data = resp.get_json()["data"]
    assert isinstance(data["request"], dict)
    assert isinstance(data["response"], dict)
    assert backend_client.get("/api/vulns").status_code == 200


def test_toggle_running_syncs_status(backend_client):
    """回归：toggle 只翻转 is_running，不同步 status，agent 无法感知停止。"""
    task = _make_task(backend_client)
    assert task["status"] == "pending"

    resp = backend_client.patch(f"/api/tasks/{task['id']}/toggle-running")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["is_running"] is True
    assert data["status"] == "running"

    resp = backend_client.patch(f"/api/tasks/{task['id']}/toggle-running")
    assert resp.get_json()["data"]["status"] == "pending"


def test_delete_task_cascades_children(backend_client):
    """回归：删除 task 后子记录变成孤儿，仍出现在全局列表与消息页。"""
    task = _make_task(backend_client)
    tid = task["id"]
    backend_client.post("/api/pages", json={"name": "p", "task_id": tid})
    backend_client.post("/api/vulns", json={"vuln_type": "XSS", "task_id": tid})
    backend_client.post("/api/messages", json={
        "session_id": tid, "role": "assistant", "content": "hi", "type": "pure",
    })

    assert backend_client.delete(f"/api/tasks/{tid}").status_code == 200

    pages = backend_client.get(f"/api/pages?task_id={tid}").get_json()["data"]
    vulns = backend_client.get(f"/api/vulns?task_id={tid}").get_json()["data"]
    messages = backend_client.get(f"/api/messages?task_id={tid}").get_json()["data"]
    assert pages == []
    assert vulns == []
    assert messages == []


def test_messages_task_and_session_filter_are_not_anded(backend_client):
    """回归：同时传 session_id 与 task_id 时两个 filter_by 叠加导致结果恒空。"""
    task = _make_task(backend_client)
    tid = task["id"]
    backend_client.post("/api/messages", json={
        "session_id": tid, "role": "assistant", "content": "hello", "type": "pure",
    })
    resp = backend_client.get(f"/api/messages?session_id={tid}&task_id={tid}")
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) >= 1


def test_process_endpoints(backend_client):
    pid = uuid.uuid4().hex
    assert backend_client.post(f"/api/process/{pid}", json={}).status_code == 201
    status = backend_client.get(f"/api/process/{pid}/status")
    assert status.status_code == 200
    assert status.get_json()["data"]["status"] == "run"

    # 回归：给不存在的 process 追加消息曾返回 400「数据完整性错误」
    missing = backend_client.post(f"/api/process/{uuid.uuid4().hex}/message", json={"metadata": {}})
    assert missing.status_code == 404, missing.get_data(as_text=True)

    # 回归：不存在时曾返回 success=True
    missing_status = backend_client.get(f"/api/process/{uuid.uuid4().hex}/status")
    assert missing_status.status_code == 404
    assert missing_status.get_json()["success"] is False
