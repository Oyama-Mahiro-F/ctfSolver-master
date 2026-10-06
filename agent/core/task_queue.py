"""
任务队列 - 管理任务优先级和依赖关系
"""
import heapq
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from utils.logger import logger


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Task:
    """任务对象"""
    id: str
    name: str
    task_type: str
    params: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID列表
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None  # 分配给哪个Agent执行
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at


class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.priority_queue: List[Task] = []  # 使用heapq实现的优先级队列
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.running_tasks: Dict[str, Task] = {}
        self.task_callbacks: Dict[str, Callable] = {}
    
    def add_task(self,
                 name: str,
                 task_type: str,
                 params: Dict[str, Any],
                 priority: TaskPriority = TaskPriority.NORMAL,
                 dependencies: Optional[List[str]] = None,
                 task_id: Optional[str] = None,
                 max_retries: int = 3) -> str:
        """
        添加任务到队列
        
        Args:
            name: 任务名称
            task_type: 任务类型
            params: 任务参数
            priority: 优先级
            dependencies: 依赖的任务ID列表
            task_id: 任务ID（自动生成如果为None）
            max_retries: 最大重试次数
            
        Returns:
            str: 任务ID
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=name,
            task_type=task_type,
            params=params,
            priority=priority,
            dependencies=dependencies or [],
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        heapq.heappush(self.priority_queue, task)
        logger.info(f"添加任务: {task_id} ({name}, 优先级: {priority.name})")
        
        return task_id
    
    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个可执行的任务（已满足依赖关系）
        
        Returns:
            Task: 下一个任务，如果没有可执行的任务返回None
        """
        # 从优先级队列中查找可执行的任务
        available_tasks = []
        
        while self.priority_queue:
            task = heapq.heappop(self.priority_queue)
            
            # 检查任务状态
            if task.status == TaskStatus.COMPLETED:
                continue
            if task.status == TaskStatus.CANCELLED:
                continue
            if task.id in self.running_tasks:
                continue
            
            # 检查依赖关系
            if self._check_dependencies(task):
                return task
            else:
                # 依赖未满足，重新加入队列
                available_tasks.append(task)
        
        # 将未满足依赖的任务重新加入队列
        for task in available_tasks:
            heapq.heappush(self.priority_queue, task)
        
        return None
    
    def _check_dependencies(self, task: Task) -> bool:
        """检查任务的依赖是否都已满足"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                logger.warning(f"任务 {task.id} 的依赖 {dep_id} 不存在")
                return False
            
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def requeue_task(self, task: Task) -> None:
        """把已从优先级队列弹出、但本次未能执行的任务重新入队。

        调度器在“没有可用 Agent”时若只 sleep+continue，任务既不在队列中
        也没在运行，会被永久丢弃（子任务依赖它时会一起卡死）。
        """
        if task.status == TaskStatus.PENDING and task.id not in self.running_tasks:
            heapq.heappush(self.priority_queue, task)

    def start_task(self, task_id: str, agent_id: Optional[str] = None) -> bool:
        """
        标记任务为运行中
        
        Args:
            task_id: 任务ID
            agent_id: 执行任务的Agent ID
            
        Returns:
            bool: 是否成功
        """
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        if task.status != TaskStatus.PENDING:
            logger.warning(f"任务 {task_id} 状态不是PENDING，无法启动")
            return False
        
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        task.agent_id = agent_id
        self.running_tasks[task_id] = task
        
        logger.info(f"启动任务: {task_id}")
        return True
    
    def complete_task(self, task_id: str, result: Any = None) -> bool:
        """
        标记任务为完成
        
        Args:
            task_id: 任务ID
            result: 任务结果
            
        Returns:
            bool: 是否成功
        """
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        if task.status != TaskStatus.RUNNING:
            logger.warning(f"任务 {task_id} 状态不是RUNNING，无法完成")
            return False
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.result = result
        
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        self.completed_tasks.append(task_id)
        
        logger.info(f"完成任务: {task_id}")
        
        # 触发回调
        if task_id in self.task_callbacks:
            try:
                self.task_callbacks[task_id](task)
            except Exception as e:
                logger.error(f"任务回调执行失败: {e}")
        
        return True
    
    def fail_task(self, task_id: str, error: str, retry: bool = True) -> bool:
        """
        标记任务为失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
            retry: 是否重试
            
        Returns:
            bool: 是否成功
        """
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        task.error = error
        
        if retry and task.retry_count < task.max_retries:
            # 重试任务
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.agent_id = None
            
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            heapq.heappush(self.priority_queue, task)
            logger.info(f"任务 {task_id} 失败，将重试 (第 {task.retry_count}/{task.max_retries} 次)")
        else:
            # 任务彻底失败
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            self.failed_tasks.append(task_id)
            logger.error(f"任务 {task_id} 失败: {error}")
        
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.CANCELLED
        
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        logger.info(f"取消任务: {task_id}")
        return True
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务列表"""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_tasks_by_type(self, task_type: str) -> List[Task]:
        """根据类型获取任务列表"""
        return [task for task in self.tasks.values() if task.task_type == task_type]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        return {
            "total": len(self.tasks),
            "pending": len(self.get_tasks_by_status(TaskStatus.PENDING)),
            "running": len(self.running_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "cancelled": len(self.get_tasks_by_status(TaskStatus.CANCELLED))
        }
    
    def register_callback(self, task_id: str, callback: Callable):
        """注册任务完成回调"""
        self.task_callbacks[task_id] = callback
    
    def clear_completed(self):
        """清理已完成的任务"""
        for task_id in self.completed_tasks:
            if task_id in self.tasks:
                del self.tasks[task_id]
        self.completed_tasks.clear()
        logger.info("已清理已完成的任务")
