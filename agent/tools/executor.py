"""
工具执行器 - 统一工具执行接口，支持Docker和本地执行
"""
import hashlib
import json
import os
import time
from functools import lru_cache
from typing import Any, Callable, Dict, Optional

from config import config
from utils.logger import logger

from .base import ToolBase, ToolResult, ToolResultStatus
from .docker_manager import DockerManager
from .registry import tool_registry


class ToolExecutor:
    """工具执行器 - 统一管理工具的执行"""
    
    def __init__(self, use_docker: bool = False, docker_image: str = "python:3.11-slim"):
        """
        初始化工具执行器
        
        Args:
            use_docker: 是否使用Docker执行（默认False，根据工具类型自动选择）
            docker_image: Docker镜像名称
        """
        self.use_docker = use_docker
        self.docker_manager = DockerManager(image=docker_image) if use_docker else None
        self.result_cache: Dict[str, ToolResult] = {}
        self.execution_stats: Dict[str, Dict] = {}
    
    def execute(self,
                tool_name: str,
                params: Dict[str, Any],
                timeout: int = 300,
                use_cache: bool = True,
                force_docker: Optional[bool] = None) -> ToolResult:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            timeout: 超时时间（秒）
            use_cache: 是否使用缓存
            force_docker: 强制使用Docker（None表示自动选择）
            
        Returns:
            ToolResult: 执行结果
        """
        start_time = time.time()
        
        # 获取工具实例
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=f"工具 {tool_name} 未找到",
                execution_time=time.time() - start_time
            )
        
        # 验证参数
        is_valid, error_msg = tool.validate_params(params)
        if not is_valid:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=error_msg,
                execution_time=time.time() - start_time
            )
        
        # 检查缓存
        if use_cache:
            cache_key = self._generate_cache_key(tool_name, params)
            if cache_key in self.result_cache:
                cached_result = self.result_cache[cache_key]
                logger.info(f"使用缓存结果: {tool_name}")
                return cached_result
        
        # 决定执行方式
        should_use_docker = force_docker if force_docker is not None else self._should_use_docker(tool_name)
        
        try:
            # 执行工具
            if should_use_docker and self.docker_manager and self.docker_manager.is_available():
                result = self._execute_in_docker(tool, params, timeout)
            else:
                result = self._execute_locally(tool, params, timeout)
            
            # 更新执行统计
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            self._update_stats(tool_name, execution_time, result.status == ToolResultStatus.SUCCESS)
            
            # 缓存结果
            if use_cache and result.status == ToolResultStatus.SUCCESS:
                cache_key = self._generate_cache_key(tool_name, params)
                self.result_cache[cache_key] = result
            
            return result
        
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 时发生异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _execute_locally(self, tool: ToolBase, params: Dict[str, Any], timeout: int) -> ToolResult:
        """本地执行工具"""
        try:
            result = tool.execute(params)
            return result
        except Exception as e:
            logger.error(f"本地执行工具失败: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _execute_in_docker(self, tool: ToolBase, params: Dict[str, Any], timeout: int) -> ToolResult:
        """在Docker容器中执行工具"""
        if not self.docker_manager or not self.docker_manager.is_available():
            logger.warning("Docker不可用，回退到本地执行")
            return self._execute_locally(tool, params, timeout)
        
        # 这里需要工具支持Docker执行模式
        # 如果工具有docker_execute方法，使用它
        if hasattr(tool, 'docker_execute'):
            try:
                result = tool.docker_execute(params, self.docker_manager, timeout)
                return result
            except Exception as e:
                logger.error(f"Docker执行工具失败: {e}")
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=str(e)
                )
        else:
            # 工具不支持Docker，回退到本地执行
            logger.warning(f"工具 {tool.name} 不支持Docker执行，使用本地执行")
            return self._execute_locally(tool, params, timeout)
    
    def _should_use_docker(self, tool_name: str) -> bool:
        """判断是否应该使用Docker执行"""
        # 危险工具列表（需要在Docker中执行）
        dangerous_tools = ['sqlmap', 'metasploit', 'nmap', 'masscan']
        
        # 检查工具名称是否包含危险工具关键字
        tool_name_lower = tool_name.lower()
        for dangerous in dangerous_tools:
            if dangerous in tool_name_lower:
                return True
        
        return False
    
    def _generate_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 对参数进行排序和序列化，确保相同参数生成相同键
        sorted_params = json.dumps(params, sort_keys=True)
        key_string = f"{tool_name}:{sorted_params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _update_stats(self, tool_name: str, execution_time: float, success: bool):
        """更新执行统计"""
        if tool_name not in self.execution_stats:
            self.execution_stats[tool_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_time": 0.0,
                "avg_time": 0.0
            }
        
        stats = self.execution_stats[tool_name]
        stats["total_executions"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["total_executions"]
        
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
    
    def get_stats(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """获取执行统计"""
        if tool_name:
            return self.execution_stats.get(tool_name, {})
        return self.execution_stats
    
    def clear_cache(self):
        """清空缓存"""
        self.result_cache.clear()
        logger.info("工具执行缓存已清空")
    
    def clear_stats(self):
        """清空统计"""
        self.execution_stats.clear()
        logger.info("工具执行统计已清空")


# 全局工具执行器实例
tool_executor = ToolExecutor(use_docker=False)  # 默认不使用Docker，可根据配置修改
