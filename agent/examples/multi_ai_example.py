"""
多AI协作系统使用示例
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orchestrator import Orchestrator, CollaborationMode
from core.knowledge_base import SharedContext
from agents.penetration import ReconAgent, ScannerAgent, ExploitAgent, PostExploitAgent
from tools.registry import tool_registry
from tools.wrappers import NmapWrapper, NucleiWrapper, SQLMapWrapper, MetasploitWrapper, FscanWrapper, ImpacketWrapper
from core.task_queue import TaskPriority
from utils.logger import logger


async def example_parallel_mode():
    """并行模式示例"""
    print("=" * 50)
    print("并行模式示例")
    print("=" * 50)
    
    # 创建协调器
    orchestrator = Orchestrator(mode=CollaborationMode.PARALLEL)
    
    # 注册Agent
    orchestrator.register_agent("recon_1", "ReconAgent-1", ["recon"], max_concurrent_tasks=2)
    orchestrator.register_agent("scanner_1", "ScannerAgent-1", ["scan"], max_concurrent_tasks=2)
    
    # 注册工具
    tool_registry.register(NmapWrapper())
    tool_registry.register(NucleiWrapper())
    
    # 注册任务处理器
    async def recon_handler(params, agent_id):
        agent = ReconAgent(agent_id, orchestrator.shared_context)
        return await agent.execute_recon(params)
    
    async def scan_handler(params, agent_id):
        agent = ScannerAgent(agent_id, orchestrator.shared_context)
        return await agent.execute_scan(params)
    
    orchestrator.register_task_handler("recon", recon_handler)
    orchestrator.register_task_handler("scan", scan_handler)
    
    # 添加任务
    task1 = orchestrator.add_task(
        name="端口扫描-192.168.1.1",
        task_type="recon",
        params={"target": "192.168.1.1", "scan_type": "port_scan"},
        priority=TaskPriority.HIGH
    )
    
    task2 = orchestrator.add_task(
        name="漏洞扫描-http://example.com",
        task_type="scan",
        params={"target": "http://example.com", "scan_type": "nuclei"},
        priority=TaskPriority.NORMAL
    )
    
    print(f"添加任务: {task1}, {task2}")
    
    # 启动协调器（在实际使用中应该运行orchestrator.run()）
    # orchestrator.start()
    # await orchestrator.run()
    
    print("并行模式示例完成")


async def example_pipeline_mode():
    """流水线模式示例"""
    print("=" * 50)
    print("流水线模式示例")
    print("=" * 50)
    
    orchestrator = Orchestrator(mode=CollaborationMode.PIPELINE)
    
    # 注册Agent
    orchestrator.register_agent("recon_1", "ReconAgent", ["recon"])
    orchestrator.register_agent("scanner_1", "ScannerAgent", ["scan"])
    orchestrator.register_agent("exploit_1", "ExploitAgent", ["exploit"])
    
    # 注册工具
    tool_registry.register(NmapWrapper())
    tool_registry.register(NucleiWrapper())
    tool_registry.register(SQLMapWrapper())
    
    # 注册任务处理器
    async def recon_handler(params, agent_id):
        agent = ReconAgent(agent_id, orchestrator.shared_context)
        return await agent.execute_recon(params)
    
    async def scan_handler(params, agent_id):
        agent = ScannerAgent(agent_id, orchestrator.shared_context)
        return await agent.execute_scan(params)
    
    async def exploit_handler(params, agent_id):
        agent = ExploitAgent(agent_id, orchestrator.shared_context)
        return await agent.execute_exploit(params)
    
    orchestrator.register_task_handler("recon", recon_handler)
    orchestrator.register_task_handler("scan", scan_handler)
    orchestrator.register_task_handler("exploit", exploit_handler)
    
    # 添加流水线任务
    task1 = orchestrator.add_task(
        name="侦察-192.168.1.0/24",
        task_type="recon",
        params={"target": "192.168.1.0/24", "scan_type": "port_scan"}
    )
    
    task2 = orchestrator.add_task(
        name="扫描-192.168.1.1",
        task_type="scan",
        params={"target": "http://192.168.1.1", "scan_type": "nuclei"},
        dependencies=[task1]  # 依赖侦察任务
    )
    
    task3 = orchestrator.add_task(
        name="利用-SQL注入",
        task_type="exploit",
        params={"target": "http://192.168.1.1", "vuln_type": "sql_injection"},
        dependencies=[task2]  # 依赖扫描任务
    )
    
    print(f"添加流水线任务: {task1} -> {task2} -> {task3}")
    print("流水线模式示例完成")


async def example_hybrid_mode():
    """混合模式示例"""
    print("=" * 50)
    print("混合模式示例")
    print("=" * 50)
    
    orchestrator = Orchestrator(mode=CollaborationMode.HYBRID)
    
    # 注册多个Agent
    orchestrator.register_agent("recon_1", "ReconAgent-1", ["recon"], max_concurrent_tasks=3)
    orchestrator.register_agent("recon_2", "ReconAgent-2", ["recon"], max_concurrent_tasks=3)
    orchestrator.register_agent("scanner_1", "ScannerAgent-1", ["scan"], max_concurrent_tasks=2)
    orchestrator.register_agent("exploit_1", "ExploitAgent-1", ["exploit"])
    orchestrator.register_agent("post_exploit_1", "PostExploitAgent-1", ["post_exploit"])
    
    # 注册所有工具
    tool_registry.register(NmapWrapper())
    tool_registry.register(NucleiWrapper())
    tool_registry.register(SQLMapWrapper())
    tool_registry.register(MetasploitWrapper())
    tool_registry.register(FscanWrapper())
    tool_registry.register(ImpacketWrapper())
    
    # 注册任务处理器
    async def recon_handler(params, agent_id):
        agent = ReconAgent(agent_id, orchestrator.shared_context)
        return await agent.execute_recon(params)
    
    async def scan_handler(params, agent_id):
        agent = ScannerAgent(agent_id, orchestrator.shared_context)
        return await agent.execute_scan(params)
    
    async def exploit_handler(params, agent_id):
        agent = ExploitAgent(agent_id, orchestrator.shared_context)
        return await agent.execute_exploit(params)
    
    async def post_exploit_handler(params, agent_id):
        agent = PostExploitAgent(agent_id, orchestrator.shared_context)
        return await agent.execute_post_exploit(params)
    
    orchestrator.register_task_handler("recon", recon_handler)
    orchestrator.register_task_handler("scan", scan_handler)
    orchestrator.register_task_handler("exploit", exploit_handler)
    orchestrator.register_task_handler("post_exploit", post_exploit_handler)
    
    # 添加多个任务（可以并行执行）
    targets = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
    recon_tasks = []
    
    for target in targets:
        task_id = orchestrator.add_task(
            name=f"侦察-{target}",
            task_type="recon",
            params={"target": target, "scan_type": "port_scan"},
            priority=TaskPriority.NORMAL
        )
        recon_tasks.append(task_id)
    
    # 扫描任务依赖所有侦察任务
    scan_task = orchestrator.add_task(
        name="扫描-所有目标",
        task_type="scan",
        params={"target": "http://192.168.1.1", "scan_type": "nuclei"},
        dependencies=recon_tasks
    )
    
    print(f"添加混合模式任务: {len(recon_tasks)}个并行侦察任务 -> 1个扫描任务")
    print("混合模式示例完成")


async def main():
    """主函数"""
    print("\n多AI协作系统使用示例\n")
    
    # 运行各种模式示例
    await example_parallel_mode()
    print()
    
    await example_pipeline_mode()
    print()
    
    await example_hybrid_mode()
    print()
    
    print("=" * 50)
    print("所有示例完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
