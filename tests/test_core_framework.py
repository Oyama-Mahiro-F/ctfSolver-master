"""core/ 多 AI 调度框架的回归测试。

该框架目前只被 agent/examples/ 引用（主流程 flaghunter 未接入），
但它的调度语义缺陷会让示例与后续接入完全不可用。
"""
import asyncio

import pytest


def test_knowledge_base_ids_are_unique(agent_path):
    """回归：毫秒时间戳做 id，同一毫秒内的条目会互相覆盖并破坏索引。"""
    from core.knowledge_base import ResultType, SharedContext

    ctx = SharedContext()
    ids = [ctx.add(entry_type=ResultType.RECON, source="a", data={"i": i}) for i in range(5)]

    assert len(set(ids)) == 5
    assert len(ctx.entries) == 5
    assert len(ctx.index_by_type[ResultType.RECON]) == 5


def test_requeue_keeps_task_schedulable(agent_path):
    """回归：调度器弹出任务后若未分配，任务会被永久丢弃。"""
    from core.task_queue import TaskQueue

    queue = TaskQueue()
    task_id = queue.add_task("t", "recon", {})

    task = queue.get_next_task()
    assert task is not None and task.id == task_id

    # 模拟“当前没有可用 Agent”
    queue.requeue_task(task)

    again = queue.get_next_task()
    assert again is not None
    assert again.id == task_id


def test_complete_requires_running(agent_path):
    """任务分解路径必须先 start_task，否则 complete_task 会失败。"""
    from core.task_queue import TaskQueue

    queue = TaskQueue()
    task_id = queue.add_task("t", "recon", {})

    assert queue.complete_task(task_id, {"x": 1}) is False
    assert queue.start_task(task_id, "master") is True
    assert queue.complete_task(task_id, {"x": 1}) is True


def test_agent_registry_does_not_expire_local_agents(agent_path):
    """回归：60 秒心跳超时且无人刷新，会把所有进程内 Agent 判为离线。"""
    from core.orchestrator import AgentRegistry

    registry = AgentRegistry()
    registry.register("a1", "Agent-1", ["recon"])

    # 默认不做过期剔除
    assert len(registry.get_available_agents()) == 1
    # 显式启用超时后才会剔除
    registry.heartbeat_timeout = 0
    assert registry.get_available_agents() == []


def test_master_orchestrator_decompose_completes_parent(agent_path):
    """回归：分解后原任务无法完成，子任务依赖永远无法满足。"""
    from core.master_orchestrator import MasterOrchestrator
    from core.task_queue import TaskStatus

    master = MasterOrchestrator()
    parent_id = master.add_task("parent", "recon", {})

    async def fake_decision(_task):
        return {
            "decompose": True,
            "sub_tasks": [{"name": "child", "type": "scan", "params": {}}],
        }

    master.make_decision = fake_decision
    master.start()
    loop = asyncio.new_event_loop()
    try:
        # 让 run() 处理父任务，然后立刻停机
        async def runner():
            run_task = asyncio.ensure_future(master.run())
            await asyncio.sleep(0.3)
            master.stop()
            await asyncio.wait_for(run_task, timeout=3)

        loop.run_until_complete(runner())
    finally:
        loop.close()

    assert master.task_queue.get_task(parent_id).status == TaskStatus.COMPLETED
    # 子任务的依赖已满足，可以被调度
    child = master.task_queue.get_next_task()
    assert child is not None
    assert child.task_type == "scan"
