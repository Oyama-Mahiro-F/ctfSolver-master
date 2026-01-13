"""
主AI协调器使用示例 - 展示"主AI调度+多AI并行"架构
"""
import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.penetration import (ExploitAgent, PostExploitAgent, ReconAgent,
                                ScannerAgent, TunnelAgent)
from core.knowledge_base import SharedContext
from core.master_orchestrator import MasterOrchestrator
from tools.registry import tool_registry
from tools.wrappers import (BloodHoundWrapper, CommixWrapper, FFufWrapper,
                            FscanWrapper, HydraWrapper, ImpacketWrapper,
                            LaZagneWrapper, LigoloWrapper, MasscanWrapper,
                            MetasploitWrapper, MimikatzWrapper, NetExecWrapper,
                            NmapWrapper, NucleiWrapper, PEASWrapper,
                            Pocsuite3Wrapper, ProxyChainsWrapper,
                            SearchSploitWrapper, SQLMapWrapper,
                            SubfinderWrapper, TplmapWrapper, WhatWebWrapper,
                            XrayWrapper, XSStrikeWrapper)
from utils.logger import logger


async def example_master_ai_orchestration():
    """主AI协调器示例 - 展示智能任务调度"""
    print("=" * 60)
    print("主AI协调器示例 - 智能任务调度和多AI并行工作")
    print("=" * 60)
    
    # 创建主AI协调器
    master_orchestrator = MasterOrchestrator()
    
    # 注册多个专业AI Agent
    master_orchestrator.register_agent("recon_1", "ReconAgent-1", ["recon"], max_concurrent_tasks=3)
    master_orchestrator.register_agent("recon_2", "ReconAgent-2", ["recon"], max_concurrent_tasks=3)
    master_orchestrator.register_agent("scanner_1", "ScannerAgent-1", ["scan"], max_concurrent_tasks=2)
    master_orchestrator.register_agent("scanner_2", "ScannerAgent-2", ["scan"], max_concurrent_tasks=2)
    master_orchestrator.register_agent("exploit_1", "ExploitAgent-1", ["exploit"], max_concurrent_tasks=2)
    master_orchestrator.register_agent("post_exploit_1", "PostExploitAgent-1", ["post_exploit"], max_concurrent_tasks=2)
    master_orchestrator.register_agent("tunnel_1", "TunnelAgent-1", ["tunnel"], max_concurrent_tasks=1)
    
    # 注册所有工具
    all_wrappers = [
        NmapWrapper(), MasscanWrapper(), SubfinderWrapper(), WhatWebWrapper(), FFufWrapper(),
        NucleiWrapper(), XrayWrapper(), SearchSploitWrapper(),
        SQLMapWrapper(), CommixWrapper(), TplmapWrapper(), XSStrikeWrapper(), HydraWrapper(),
        MetasploitWrapper(), Pocsuite3Wrapper(),
        PEASWrapper(), MimikatzWrapper(), LaZagneWrapper(),
        FscanWrapper(), ImpacketWrapper(), NetExecWrapper(), BloodHoundWrapper(),
        LigoloWrapper(), ProxyChainsWrapper()
    ]
    
    for wrapper in all_wrappers:
        if not tool_registry.get_tool(wrapper.name):
            tool_registry.register(wrapper)
    
    # 注册任务处理器
    async def recon_handler(params, agent_id):
        agent = ReconAgent(agent_id, master_orchestrator.shared_context)
        return await agent.execute_recon(params)
    
    async def scan_handler(params, agent_id):
        agent = ScannerAgent(agent_id, master_orchestrator.shared_context)
        return await agent.execute_scan(params)
    
    async def exploit_handler(params, agent_id):
        agent = ExploitAgent(agent_id, master_orchestrator.shared_context)
        return await agent.execute_exploit(params)
    
    async def post_exploit_handler(params, agent_id):
        agent = PostExploitAgent(agent_id, master_orchestrator.shared_context)
        return await agent.execute_post_exploit(params)
    
    async def tunnel_handler(params, agent_id):
        agent = TunnelAgent(agent_id, master_orchestrator.shared_context)
        return await agent.execute_tunnel(params)
    
    master_orchestrator.register_task_handler("recon", recon_handler)
    master_orchestrator.register_task_handler("scan", scan_handler)
    master_orchestrator.register_task_handler("exploit", exploit_handler)
    master_orchestrator.register_task_handler("post_exploit", post_exploit_handler)
    master_orchestrator.register_task_handler("tunnel", tunnel_handler)
    
    # 添加多个任务 - 主AI将智能分配
    print("\n添加任务到队列...")
    
    # 侦察任务（可以并行执行）
    task1 = master_orchestrator.add_task(
        name="端口扫描-192.168.1.1",
        task_type="recon",
        params={"target": "192.168.1.1", "scan_type": "port_scan"},
    )
    
    task2 = master_orchestrator.add_task(
        name="子域名枚举-example.com",
        task_type="recon",
        params={"target": "example.com", "scan_type": "subdomain"},
    )
    
    task3 = master_orchestrator.add_task(
        name="Web指纹识别-http://example.com",
        task_type="recon",
        params={"target": "http://example.com", "scan_type": "fingerprint"},
    )
    
    # 扫描任务（依赖侦察任务）
    task4 = master_orchestrator.add_task(
        name="漏洞扫描-http://example.com",
        task_type="scan",
        params={"target": "http://example.com", "scan_type": "nuclei"},
        dependencies=[task1, task3]  # 依赖侦察任务
    )
    
    # 利用任务（依赖扫描任务）
    task5 = master_orchestrator.add_task(
        name="SQL注入利用",
        task_type="exploit",
        params={
            "target": "http://example.com",
            "vuln_type": "sql_injection",
            "vuln_info": {"id": "vuln_001"}
        },
        dependencies=[task4]
    )
    
    print(f"已添加任务: {task1}, {task2}, {task3}, {task4}, {task5}")
    print("\n主AI协调器将智能分析任务并分配给合适的Agent...")
    print("多个Agent将并行工作，共享发现结果...")
    
    # 启动主AI协调器（在实际使用中）
    # master_orchestrator.start()
    # await master_orchestrator.run()
    
    # 获取统计信息
    stats = master_orchestrator.get_statistics()
    print(f"\n系统统计: {stats}")
    
    print("\n主AI协调器示例完成")


async def example_all_tools():
    """展示所有工具的使用"""
    print("=" * 60)
    print("所有工具使用示例")
    print("=" * 60)
    
    from tools.executor import tool_executor

    # 注册所有工具
    all_wrappers = [
        NmapWrapper(), MasscanWrapper(), SubfinderWrapper(), WhatWebWrapper(), FFufWrapper(),
        NucleiWrapper(), XrayWrapper(), SearchSploitWrapper(),
        SQLMapWrapper(), CommixWrapper(), TplmapWrapper(), XSStrikeWrapper(), HydraWrapper(),
        MetasploitWrapper(), Pocsuite3Wrapper(),
        PEASWrapper(), MimikatzWrapper(), LaZagneWrapper(),
        FscanWrapper(), ImpacketWrapper(), NetExecWrapper(), BloodHoundWrapper(),
        LigoloWrapper(), ProxyChainsWrapper()
    ]
    
    for wrapper in all_wrappers:
        if not tool_registry.get_tool(wrapper.name):
            tool_registry.register(wrapper)
    
    print("\n已注册的工具:")
    for tool_name in tool_registry.list_tools():
        schema = tool_registry.get_tool_schema(tool_name)
        if schema:
            print(f"  - {tool_name}: {schema.get('description', 'N/A')}")
    
    print(f"\n总共注册了 {len(tool_registry.list_tools())} 个工具")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("多AI协作渗透测试系统 - 完整功能演示")
    print("=" * 60 + "\n")
    
    # 运行主AI协调器示例
    await example_master_ai_orchestration()
    print()
    
    # 展示所有工具
    await example_all_tools()
    print()
    
    print("=" * 60)
    print("演示完成")
    print("=" * 60)
    print("\n架构说明:")
    print("1. 主AI协调器（MasterOrchestrator）使用LLM进行智能任务调度")
    print("2. 多个专业AI Agent并行工作（Recon, Scanner, Exploit等）")
    print("3. 所有Agent共享知识库，避免重复工作")
    print("4. 所有工具输出标准化为JSON格式，便于AI理解")
    print("5. 支持7个阶段的完整渗透测试流程")


if __name__ == "__main__":
    asyncio.run(main())
