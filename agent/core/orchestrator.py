"""
多AI协作引擎 - 协调多个AI Agent的工作模式
"""
import asyncio
import heapq
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from utils.logger import logger

from .knowledge_base import ResultAggregator, ResultType, SharedContext
from .task_queue import Task, TaskPriority, TaskQueue, TaskStatus


class CollaborationMode(Enum):
    """协作模式"""
    PARALLEL = "parallel"  # 并行模式
    PIPELINE = "pipeline"  # 流水线模式
    ORCHESTRATED = "orchestrated"  # 编排模式
    HYBRID = "hybrid"  # 混合模式


@dataclass
class AgentCapability:
    """Agent能力描述"""
    agent_id: str
    agent_name: str
    capabilities: List[str]  # 能力列表，如 ["recon", "scan", "exploit"]
    max_concurrent_tasks: int = 1
    current_tasks: int = 0
    status: str = "idle"  # idle, busy, error
    last_heartbeat: float = 0


class AgentRegistry:
    """Agent注册表 - 管理所有注册的AI Agent"""
    
    def __init__(self, heartbeat_timeout: Optional[float] = None):
        self.agents: Dict[str, AgentCapability] = {}
        self.agent_callbacks: Dict[str, Callable] = {}
        # None 表示不做过期剔除：本框架的 Agent 都在当前进程内注册、始终存活。
        # 原实现硬编码 60 秒超时且无人调用 update_heartbeat，
        # 注册 60 秒后所有 Agent 都被判为 error，调度永久停摆。
        self.heartbeat_timeout = heartbeat_timeout
    
    def register(self,
                 agent_id: str,
                 agent_name: str,
                 capabilities: List[str],
                 max_concurrent_tasks: int = 1) -> bool:
        """
        注册Agent
        
        Args:
            agent_id: Agent ID
            agent_name: Agent名称
            capabilities: 能力列表
            max_concurrent_tasks: 最大并发任务数
            
        Returns:
            bool: 是否成功
        """
        if agent_id in self.agents:
            logger.warning(f"Agent {agent_id} 已存在，将被覆盖")
        
        capability = AgentCapability(
            agent_id=agent_id,
            agent_name=agent_name,
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent_tasks,
            last_heartbeat=time.time()
        )
        
        self.agents[agent_id] = capability
        logger.info(f"注册Agent: {agent_id} ({agent_name}), 能力: {capabilities}")
        return True
    
    def unregister(self, agent_id: str) -> bool:
        """取消注册Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"取消注册Agent: {agent_id}")
            return True
        return False
    
    def update_heartbeat(self, agent_id: str):
        """更新Agent心跳"""
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = time.time()
            self.agents[agent_id].status = "idle" if self.agents[agent_id].current_tasks == 0 else "busy"
    
    def get_available_agents(self, capability: Optional[str] = None) -> List[AgentCapability]:
        """
        获取可用的Agent列表
        
        Args:
            capability: 所需能力（None表示任意）
            
        Returns:
            List[AgentCapability]: 可用Agent列表
        """
        available = []
        current_time = time.time()
        
        for agent in self.agents.values():
            # 心跳过期检查（默认关闭，见 __init__ 注释）
            if (self.heartbeat_timeout is not None
                    and current_time - agent.last_heartbeat >= self.heartbeat_timeout):
                agent.status = "error"
                continue
            
            # 检查能力
            if capability and capability not in agent.capabilities:
                continue
            
            # 检查是否还有空闲槽位
            if agent.current_tasks >= agent.max_concurrent_tasks:
                continue
            
            # 检查状态
            if agent.status == "error":
                continue
            
            available.append(agent)
        
        return available
    
    def assign_task(self, agent_id: str) -> bool:
        """分配任务给Agent"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        if agent.current_tasks >= agent.max_concurrent_tasks:
            return False
        
        agent.current_tasks += 1
        agent.status = "busy"
        # 任务分配即视为该 Agent 存活，刷新心跳
        self.update_heartbeat(agent_id)
        return True
    
    def release_task(self, agent_id: str):
        """释放Agent的任务"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        if agent.current_tasks > 0:
            agent.current_tasks -= 1
        if agent.current_tasks == 0:
            agent.status = "idle"
        self.update_heartbeat(agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[AgentCapability]:
        """获取Agent"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[AgentCapability]:
        """列出所有Agent"""
        return list(self.agents.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.agents)
        idle = sum(1 for a in self.agents.values() if a.status == "idle")
        busy = sum(1 for a in self.agents.values() if a.status == "busy")
        error = sum(1 for a in self.agents.values() if a.status == "error")
        
        return {
            "total": total,
            "idle": idle,
            "busy": busy,
            "error": error,
            "total_tasks": sum(a.current_tasks for a in self.agents.values())
        }


class Orchestrator:
    """主协调器 - 支持多种协作模式"""
    
    def __init__(self,
                 mode: CollaborationMode = CollaborationMode.HYBRID,
                 shared_context: Optional[SharedContext] = None):
        """
        初始化协调器
        
        Args:
            mode: 协作模式
            shared_context: 共享上下文（如果为None则创建新的）
        """
        self.mode = mode
        self.shared_context = shared_context or SharedContext()
        self.agent_registry = AgentRegistry()
        self.task_queue = TaskQueue()
        self.result_aggregator = ResultAggregator(self.shared_context)
        self.is_running = False
        self.task_handlers: Dict[str, Callable] = {}
    
    def register_agent(self,
                      agent_id: str,
                      agent_name: str,
                      capabilities: List[str],
                      max_concurrent_tasks: int = 1) -> bool:
        """注册Agent"""
        return self.agent_registry.register(agent_id, agent_name, capabilities, max_concurrent_tasks)
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        logger.info(f"注册任务处理器: {task_type}")
    
    def add_task(self,
                 name: str,
                 task_type: str,
                 params: Dict[str, Any],
                 priority: TaskPriority = TaskPriority.NORMAL,
                 dependencies: Optional[List[str]] = None) -> str:
        """添加任务"""
        return self.task_queue.add_task(name, task_type, params, priority, dependencies)
    
    def start(self):
        """启动协调器"""
        self.is_running = True
        logger.info(f"启动协调器 (模式: {self.mode.value})")
    
    def stop(self):
        """停止协调器"""
        self.is_running = False
        logger.info("停止协调器")
    
    async def run_parallel_mode(self):
        """并行模式 - 多个Agent同时执行独立任务"""
        logger.info("运行并行模式")
        
        while self.is_running:
            # 获取下一个可执行的任务
            task = self.task_queue.get_next_task()
            if not task:
                await asyncio.sleep(1)
                continue
            
            # 查找可用的Agent
            available_agents = self.agent_registry.get_available_agents()
            if not available_agents:
                # 没有可用Agent，将任务重新加入队列
                heapq.heappush(self.task_queue.priority_queue, task)
                await asyncio.sleep(1)
                continue
            
            # 选择最合适的Agent（负载均衡）
            selected_agent = min(available_agents, key=lambda a: a.current_tasks)
            
            # 分配任务
            if self.agent_registry.assign_task(selected_agent.agent_id):
                self.task_queue.start_task(task.id, selected_agent.agent_id)
                
                # 异步执行任务
                asyncio.create_task(self._execute_task(task, selected_agent.agent_id))
            
            await asyncio.sleep(0.1)  # 避免CPU占用过高
    
    async def run_pipeline_mode(self):
        """流水线模式 - 按阶段顺序执行"""
        logger.info("运行流水线模式")
        
        stages = ["recon", "scan", "exploit", "post_exploit"]
        current_stage_index = 0
        
        while self.is_running:
            current_stage = stages[current_stage_index]
            
            # 获取当前阶段的任务
            stage_tasks = [
                t for t in self.task_queue.get_tasks_by_type(current_stage)
                if t.status == TaskStatus.PENDING
            ]
            
            if not stage_tasks:
                # 当前阶段没有待执行任务：直接推进到下一阶段。
                # 原实现要求“该阶段必须有已完成任务”才推进，
                # 当某阶段完全没有任务时（例如只有 scan/exploit）会永久卡死。
                if current_stage_index < len(stages) - 1:
                    current_stage_index += 1
                    logger.info(f"进入下一阶段: {stages[current_stage_index]}")
                else:
                    await asyncio.sleep(1)
                continue
            
            # 执行当前阶段的任务
            for task in stage_tasks[:5]:  # 每次最多处理5个任务
                available_agents = self.agent_registry.get_available_agents(current_stage)
                if available_agents:
                    selected_agent = min(available_agents, key=lambda a: a.current_tasks)
                    if self.agent_registry.assign_task(selected_agent.agent_id):
                        self.task_queue.start_task(task.id, selected_agent.agent_id)
                        asyncio.create_task(self._execute_task(task, selected_agent.agent_id))
            
            await asyncio.sleep(0.5)
    
    async def run_orchestrated_mode(self):
        """编排模式 - 主AI根据任务动态分配"""
        logger.info("运行编排模式")
        
        # 查找主协调Agent
        master_agents = self.agent_registry.get_available_agents("orchestrator")
        if not master_agents:
            logger.warning("未找到主协调Agent，回退到并行模式")
            await self.run_parallel_mode()
            return
        
        # 主协调Agent负责决策任务分配
        while self.is_running:
            task = self.task_queue.get_next_task()
            if not task:
                await asyncio.sleep(1)
                continue
            
            # 让主协调Agent决定如何分配任务
            # 这里简化处理，实际应该调用主Agent的决策函数
            available_agents = self.agent_registry.get_available_agents()
            assigned = False
            if available_agents:
                # 选择最合适的Agent
                selected_agent = min(available_agents, key=lambda a: a.current_tasks)
                if self.agent_registry.assign_task(selected_agent.agent_id):
                    self.task_queue.start_task(task.id, selected_agent.agent_id)
                    asyncio.create_task(self._execute_task(task, selected_agent.agent_id))
                    assigned = True
            if not assigned:
                # 未能分配时必须重新入队，否则任务被弹出后永久丢失
                self.task_queue.requeue_task(task)
            
            await asyncio.sleep(0.1)
    
    async def run_hybrid_mode(self):
        """混合模式 - 结合多种模式"""
        logger.info("运行混合模式")
        
        # 根据任务类型选择不同的执行策略
        while self.is_running:
            task = self.task_queue.get_next_task()
            if not task:
                await asyncio.sleep(1)
                continue
            
            # 根据任务类型选择 Agent（recon/scan 可并行，其余同样按能力匹配）
            available_agents = self.agent_registry.get_available_agents(task.task_type)
            assigned = False
            if available_agents:
                selected_agent = min(available_agents, key=lambda a: a.current_tasks)
                if self.agent_registry.assign_task(selected_agent.agent_id):
                    self.task_queue.start_task(task.id, selected_agent.agent_id)
                    asyncio.create_task(self._execute_task(task, selected_agent.agent_id))
                    assigned = True
            if not assigned:
                # 原实现在能力不匹配时只 sleep，任务被丢弃且永不重试
                self.task_queue.requeue_task(task)
            
            await asyncio.sleep(0.1)
    
    async def _execute_task(self, task: Task, agent_id: str):
        """执行任务"""
        try:
            # 查找任务处理器
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                logger.error(f"未找到任务处理器: {task.task_type}")
                self.task_queue.fail_task(task.id, f"未找到任务处理器: {task.task_type}", retry=False)
                return
            
            # 执行任务
            result = await handler(task.params, agent_id)
            
            # 保存结果到共享上下文
            result_type = self._map_task_type_to_result_type(task.task_type)
            entry_id = self.shared_context.add(
                entry_type=result_type,
                source=agent_id,
                data=result if isinstance(result, dict) else {"result": result}
            )
            
            # 完成任务
            self.task_queue.complete_task(task.id, result)
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            self.task_queue.fail_task(task.id, str(e), retry=True)
        finally:
            # 释放Agent
            self.agent_registry.release_task(agent_id)
    
    def _map_task_type_to_result_type(self, task_type: str) -> ResultType:
        """映射任务类型到结果类型"""
        mapping = {
            "recon": ResultType.RECON,
            "scan": ResultType.VULN,
            "exploit": ResultType.EXPLOIT,
            "post_exploit": ResultType.POST_EXPLOIT,
            "tunnel": ResultType.TUNNEL,
        }
        return mapping.get(task_type, ResultType.GENERAL)
    
    async def run(self):
        """运行协调器（根据模式选择执行方法）"""
        if self.mode == CollaborationMode.PARALLEL:
            await self.run_parallel_mode()
        elif self.mode == CollaborationMode.PIPELINE:
            await self.run_pipeline_mode()
        elif self.mode == CollaborationMode.ORCHESTRATED:
            await self.run_orchestrated_mode()
        else:  # HYBRID
            await self.run_hybrid_mode()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "mode": self.mode.value,
            "agents": self.agent_registry.get_statistics(),
            "tasks": self.task_queue.get_statistics(),
            "knowledge_base": {
                "total_entries": len(self.shared_context.entries),
                "by_type": {rt.value: len(self.shared_context.index_by_type[rt]) for rt in ResultType}
            }
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        return {
            "statistics": self.get_statistics(),
            "recon_summary": self.result_aggregator.aggregate_recon_results(),
            "vuln_summary": self.result_aggregator.aggregate_vuln_results(),
            "key_paths": self.result_aggregator.identify_key_paths(),
            "full_report": self.result_aggregator.generate_report()
        }
