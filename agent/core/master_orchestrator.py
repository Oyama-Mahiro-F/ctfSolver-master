"""
主AI协调器 - 使用LLM进行智能任务调度和决策
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from .orchestrator import Orchestrator, CollaborationMode, AgentRegistry
from .knowledge_base import SharedContext, ResultAggregator, ResultType
from .task_queue import TaskQueue, Task, TaskPriority
from utils.chatbot import chat, add_message
from utils.logger import logger
from config import config


class MasterOrchestrator:
    """主AI协调器 - 使用LLM进行智能任务调度"""
    
    def __init__(self, shared_context: Optional[SharedContext] = None):
        """
        初始化主AI协调器
        
        Args:
            shared_context: 共享上下文
        """
        self.shared_context = shared_context or SharedContext()
        self.agent_registry = AgentRegistry()
        self.task_queue = TaskQueue()
        self.result_aggregator = ResultAggregator(self.shared_context)
        self.is_running = False
        self.task_handlers: Dict[str, Any] = {}
        self.decision_session_id: Optional[str] = None
    
    def register_agent(self,
                      agent_id: str,
                      agent_name: str,
                      capabilities: List[str],
                      max_concurrent_tasks: int = 1) -> bool:
        """注册Agent"""
        return self.agent_registry.register(agent_id, agent_name, capabilities, max_concurrent_tasks)
    
    def register_task_handler(self, task_type: str, handler: Any):
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
        """启动主AI协调器"""
        self.is_running = True
        # 创建决策会话
        self.decision_session_id = add_message("主AI协调器已启动，准备进行智能任务调度")
        logger.info("主AI协调器已启动")
    
    def stop(self):
        """停止主AI协调器"""
        self.is_running = False
        logger.info("主AI协调器已停止")
    
    async def make_decision(self, task: Task) -> Dict[str, Any]:
        """
        使用LLM进行任务分配决策
        
        Args:
            task: 待分配的任务
            
        Returns:
            Dict: 决策结果，包含分配的agent_id和策略
        """
        # 构建决策上下文
        context = {
            "task": {
                "id": task.id,
                "name": task.name,
                "type": task.task_type,
                "params": task.params,
                "priority": task.priority.name,
                "dependencies": task.dependencies
            },
            "available_agents": [
                {
                    "id": agent.agent_id,
                    "name": agent.agent_name,
                    "capabilities": agent.capabilities,
                    "current_tasks": agent.current_tasks,
                    "max_concurrent": agent.max_concurrent_tasks,
                    "status": agent.status
                }
                for agent in self.agent_registry.get_available_agents()
            ],
            "knowledge_base_summary": {
                "total_entries": len(self.shared_context.entries),
                "recent_findings": [
                    {
                        "type": entry.type.value,
                        "source": entry.source,
                        "summary": str(entry.data)[:200]  # 摘要
                    }
                    for entry in self.shared_context.query(limit=10)
                ]
            },
            "queue_status": self.task_queue.get_statistics()
        }
        
        # 构建LLM提示词
        prompt = self._build_decision_prompt(context)
        
        # 调用LLM进行决策
        try:
            response = chat(prompt, self.decision_session_id or "master_ai")
            
            # 解析LLM响应
            decision = self._parse_decision(response, context)
            return decision
        
        except Exception as e:
            logger.error(f"LLM决策失败: {e}")
            # 回退到简单规则
            return self._fallback_decision(task, context)
    
    def _build_decision_prompt(self, context: Dict[str, Any]) -> str:
        """构建决策提示词"""
        prompt = f"""你是一个智能任务调度系统的主AI协调器。你需要分析任务并决定如何分配给合适的Agent。

当前任务信息：
- 任务ID: {context['task']['id']}
- 任务名称: {context['task']['name']}
- 任务类型: {context['task']['type']}
- 任务参数: {json.dumps(context['task']['params'], ensure_ascii=False, indent=2)}
- 优先级: {context['task']['priority']}
- 依赖任务: {context['task']['dependencies']}

可用Agent列表：
{json.dumps(context['available_agents'], ensure_ascii=False, indent=2)}

知识库摘要（最近的发现）：
{json.dumps(context['knowledge_base_summary'], ensure_ascii=False, indent=2)}

任务队列状态：
{json.dumps(context['queue_status'], ensure_ascii=False, indent=2)}

请分析任务并做出决策，返回JSON格式：
{{
    "agent_id": "选择的Agent ID",
    "reasoning": "选择该Agent的原因",
    "strategy": "执行策略说明",
    "parallel_tasks": ["可以并行执行的其他任务ID列表"],
    "estimated_time": "预估执行时间（秒）"
}}

如果任务需要分解为多个子任务，返回：
{{
    "decompose": true,
    "sub_tasks": [
        {{"name": "子任务1", "type": "recon", "params": {{}}}},
        {{"name": "子任务2", "type": "scan", "params": {{}}}}
    ]
}}

请只返回JSON，不要其他内容。"""
        return prompt
    
    def _parse_decision(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """解析LLM决策响应"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                # 如果没有找到JSON，尝试直接解析
                decision = json.loads(response)
            
            # 验证决策
            if "decompose" in decision and decision["decompose"]:
                return decision
            
            if "agent_id" not in decision:
                raise ValueError("决策中缺少agent_id")
            
            # 验证agent_id是否有效
            available_agent_ids = [a["id"] for a in context["available_agents"]]
            if decision["agent_id"] not in available_agent_ids:
                logger.warning(f"LLM选择的Agent {decision['agent_id']} 不可用，使用回退策略")
                return self._fallback_decision(
                    Task(id=context["task"]["id"], name=context["task"]["name"],
                         task_type=context["task"]["type"], params=context["task"]["params"]),
                    context
                )
            
            return decision
        
        except Exception as e:
            logger.error(f"解析LLM决策失败: {e}, 响应: {response[:200]}")
            return self._fallback_decision(
                Task(id=context["task"]["id"], name=context["task"]["name"],
                     task_type=context["task"]["type"], params=context["task"]["params"]),
                context
            )
    
    def _fallback_decision(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """回退决策（基于规则）"""
        # 根据任务类型选择Agent
        task_type = task.task_type
        
        # 查找有对应能力的Agent
        available_agents = self.agent_registry.get_available_agents(task_type)
        if available_agents:
            # 选择负载最低的Agent
            selected_agent = min(available_agents, key=lambda a: a.current_tasks)
            return {
                "agent_id": selected_agent.agent_id,
                "reasoning": f"基于规则：任务类型 {task_type} 匹配Agent能力",
                "strategy": "直接执行",
                "parallel_tasks": [],
                "estimated_time": 300
            }
        
        # 如果没有匹配的Agent，选择任意可用Agent
        all_available = self.agent_registry.get_available_agents()
        if all_available:
            selected_agent = min(all_available, key=lambda a: a.current_tasks)
            return {
                "agent_id": selected_agent.agent_id,
                "reasoning": "回退：选择负载最低的可用Agent",
                "strategy": "直接执行",
                "parallel_tasks": [],
                "estimated_time": 300
            }
        
        return {
            "agent_id": None,
            "reasoning": "没有可用Agent",
            "strategy": "等待",
            "parallel_tasks": [],
            "estimated_time": 0
        }
    
    async def run(self):
        """运行主AI协调器"""
        logger.info("主AI协调器开始运行")
        
        while self.is_running:
            # 获取下一个可执行的任务
            task = self.task_queue.get_next_task()
            if not task:
                await asyncio.sleep(1)
                continue
            
            # 使用LLM进行决策
            decision = await self.make_decision(task)
            
            # 处理任务分解
            if decision.get("decompose"):
                logger.info(f"任务 {task.id} 需要分解为子任务")
                sub_tasks = decision.get("sub_tasks", [])
                for sub_task in sub_tasks:
                    self.add_task(
                        name=sub_task["name"],
                        task_type=sub_task["type"],
                        params=sub_task.get("params", {}),
                        dependencies=[task.id]
                    )
                # 标记原任务为完成（已分解）
                self.task_queue.complete_task(task.id, {"decomposed": True, "sub_tasks": sub_tasks})
                continue
            
            # 分配任务给Agent
            agent_id = decision.get("agent_id")
            if not agent_id:
                logger.warning(f"无法为任务 {task.id} 分配Agent，稍后重试")
                await asyncio.sleep(5)
                continue
            
            # 检查Agent是否可用
            agent = self.agent_registry.get_agent(agent_id)
            if not agent or agent.current_tasks >= agent.max_concurrent_tasks:
                logger.warning(f"Agent {agent_id} 不可用，稍后重试")
                await asyncio.sleep(1)
                continue
            
            # 分配任务
            if self.agent_registry.assign_task(agent_id):
                self.task_queue.start_task(task.id, agent_id)
                logger.info(f"任务 {task.id} 分配给Agent {agent_id}，原因: {decision.get('reasoning', 'N/A')}")
                
                # 异步执行任务
                asyncio.create_task(self._execute_task(task, agent_id))
            
            # 处理并行任务
            parallel_tasks = decision.get("parallel_tasks", [])
            for parallel_task_id in parallel_tasks:
                parallel_task = self.task_queue.get_task(parallel_task_id)
                if parallel_task and parallel_task.status.value == "pending":
                    # 为并行任务也进行决策和分配
                    parallel_decision = await self.make_decision(parallel_task)
                    parallel_agent_id = parallel_decision.get("agent_id")
                    if parallel_agent_id and self.agent_registry.assign_task(parallel_agent_id):
                        self.task_queue.start_task(parallel_task_id, parallel_agent_id)
                        asyncio.create_task(self._execute_task(parallel_task, parallel_agent_id))
            
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
                data=result if isinstance(result, dict) else {"result": result},
                tags=[task.task_type, task.name]
            )
            
            # 完成任务
            self.task_queue.complete_task(task.id, result)
            logger.info(f"任务 {task.id} 执行完成，结果已保存到知识库: {entry_id}")
        
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
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
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
