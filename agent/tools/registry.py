"""
工具注册系统 - 动态发现和管理工具
"""
import importlib
import inspect
import os
from typing import Dict, List, Optional, Type

from utils.logger import logger

from .base import ToolBase


class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""
    
    def __init__(self):
        self._tools: Dict[str, ToolBase] = {}
        self._tool_classes: Dict[str, Type[ToolBase]] = {}
        self._tool_paths: Dict[str, str] = {}
    
    def register(self, tool: ToolBase, tool_path: Optional[str] = None):
        """
        注册工具
        
        Args:
            tool: 工具实例
            tool_path: 工具文件路径（用于调试）
        """
        if not isinstance(tool, ToolBase):
            raise ValueError(f"工具必须继承ToolBase类: {tool}")
        
        if tool.name in self._tools:
            logger.warning(f"工具 {tool.name} 已存在，将被覆盖")
        
        self._tools[tool.name] = tool
        self._tool_paths[tool.name] = tool_path or "unknown"
        logger.info(f"注册工具: {tool.name} - {tool.description}")
    
    def register_class(self, tool_class: Type[ToolBase], tool_path: Optional[str] = None):
        """
        注册工具类（延迟实例化）
        
        Args:
            tool_class: 工具类
            tool_path: 工具文件路径
        """
        if not issubclass(tool_class, ToolBase):
            raise ValueError(f"工具类必须继承ToolBase: {tool_class}")
        
        # 尝试实例化以获取工具名称
        try:
            instance = tool_class()
            tool_name = instance.name
        except Exception as e:
            logger.error(f"无法实例化工具类 {tool_class}: {e}")
            return
        
        self._tool_classes[tool_name] = tool_class
        self._tool_paths[tool_name] = tool_path or "unknown"
        logger.info(f"注册工具类: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[ToolBase]:
        """
        获取工具实例
        
        Args:
            tool_name: 工具名称
            
        Returns:
            ToolBase: 工具实例，如果不存在返回None
        """
        # 先检查已实例化的工具
        if tool_name in self._tools:
            return self._tools[tool_name]
        
        # 检查工具类，延迟实例化
        if tool_name in self._tool_classes:
            try:
                tool_class = self._tool_classes[tool_name]
                tool = tool_class()
                self._tools[tool_name] = tool  # 缓存实例
                return tool
            except Exception as e:
                logger.error(f"实例化工具 {tool_name} 失败: {e}")
                return None
        
        return None
    
    def list_tools(self) -> List[str]:
        """列出所有已注册的工具名称"""
        all_tools = set(self._tools.keys()) | set(self._tool_classes.keys())
        return sorted(list(all_tools))
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """获取工具的模式描述"""
        tool = self.get_tool(tool_name)
        if tool:
            return tool.get_schema()
        return None
    
    def get_all_schemas(self) -> Dict[str, Dict]:
        """获取所有工具的模式描述"""
        schemas = {}
        for tool_name in self.list_tools():
            schema = self.get_tool_schema(tool_name)
            if schema:
                schemas[tool_name] = schema
        return schemas
    
    def auto_discover(self, directory: str, package_prefix: str = ""):
        """
        自动发现并注册工具
        
        Args:
            directory: 工具目录路径
            package_prefix: Python包前缀（如 "tools.wrappers"）
        """
        if not os.path.exists(directory):
            logger.warning(f"工具目录不存在: {directory}")
            return
        
        # 遍历目录查找Python文件
        for filename in os.listdir(directory):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue
            
            module_name = filename[:-3]  # 移除.py后缀
            full_module_name = f"{package_prefix}.{module_name}" if package_prefix else module_name
            
            try:
                # 动态导入模块
                if package_prefix:
                    module = importlib.import_module(full_module_name)
                else:
                    # 如果是在tools目录下，需要从tools包导入
                    module = importlib.import_module(f"tools.{module_name}")
                
                # 查找所有ToolBase的子类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, ToolBase) and 
                        obj != ToolBase):
                        try:
                            self.register_class(obj, os.path.join(directory, filename))
                        except Exception as e:
                            logger.error(f"注册工具类 {name} 失败: {e}")
            
            except Exception as e:
                logger.error(f"导入模块 {full_module_name} 失败: {e}")
    
    def unregister(self, tool_name: str):
        """取消注册工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]
        if tool_name in self._tool_classes:
            del self._tool_classes[tool_name]
        if tool_name in self._tool_paths:
            del self._tool_paths[tool_name]
        logger.info(f"取消注册工具: {tool_name}")
    
    def check_dependencies(self, tool_name: str) -> tuple[bool, List[str]]:
        """
        检查工具依赖
        
        Returns:
            tuple: (是否满足依赖, 缺失的依赖列表)
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return False, [f"工具 {tool_name} 不存在"]
        
        # 这里可以添加具体的依赖检查逻辑
        # 例如检查系统命令、Python包等
        missing = []
        
        # 示例：检查工具是否有check_dependencies方法
        if hasattr(tool, 'check_dependencies'):
            missing = tool.check_dependencies()
        
        return len(missing) == 0, missing


# 全局工具注册表实例
tool_registry = ToolRegistry()
