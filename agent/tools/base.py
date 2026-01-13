"""
工具基类 - 定义所有工具的通用接口
"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ToolResultStatus(Enum):
    """工具执行结果状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ToolResult:
    """工具执行结果"""
    status: ToolResultStatus
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    raw_output: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "raw_output": self.raw_output
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ToolBase(ABC):
    """工具基类 - 所有工具必须继承此类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.required_params = []
        self.optional_params = []
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行工具
        
        Args:
            params: 工具参数字典
            
        Returns:
            ToolResult: 执行结果
        """
        pass
    
    @abstractmethod
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """
        解析工具输出为JSON格式
        
        Args:
            raw_output: 工具原始输出
            
        Returns:
            Dict: 解析后的JSON数据
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证参数
        
        Args:
            params: 参数字典
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        # 检查必需参数
        for param in self.required_params:
            if param not in params:
                return False, f"缺少必需参数: {param}"
        
        return True, None
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的参数模式（用于AI理解工具能力）
        
        Returns:
            Dict: 工具模式描述
        """
        return {
            "name": self.name,
            "description": self.description,
            "required_params": self.required_params,
            "optional_params": self.optional_params
        }
    
    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
