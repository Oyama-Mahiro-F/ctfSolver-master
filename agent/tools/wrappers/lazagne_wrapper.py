"""
LaZagne包装器 - 跨平台密码抓取
"""
import os
import subprocess
import json
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class LaZagneWrapper(ToolBase):
    """LaZagne工具包装器（跨平台）"""
    
    def __init__(self):
        super().__init__(
            name="lazagne",
            description="跨平台密码抓取工具"
        )
        self.required_params = ["target", "module"]
        self.optional_params = ["credentials"]
        self.lazagne_path = get_tool_path("lazagne") or "laZagne"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行LaZagne"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # IP地址
            module = params["module"]  # all, browsers, wifi, etc.
            credentials = params.get("credentials")
            
            # 构建LaZagne命令
            cmd = [self.lazagne_path, module]
            
            # JSON输出
            cmd.append("-oJ")
            
            # 执行命令（需要在目标机器上执行）
            logger.info(f"执行LaZagne: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout)
            
            if result.returncode == 0 or parsed_data.get("credentials"):
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    data=parsed_data,
                    raw_output=result.stdout
                )
            else:
                return ToolResult(
                    status=ToolResultStatus.FAILURE,
                    error=result.stderr,
                    data=parsed_data if parsed_data else None
                )
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolResultStatus.TIMEOUT,
                error="LaZagne执行超时"
            )
        except Exception as e:
            logger.error(f"LaZagne执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析LaZagne JSON输出"""
        result = {
            "credentials": [],
            "summary": {
                "total": 0,
                "by_module": {}
            }
        }
        
        try:
            data = json.loads(output)
            for module_name, module_data in data.items():
                if isinstance(module_data, list):
                    for cred in module_data:
                        result["credentials"].append({
                            "module": module_name,
                            "username": cred.get("Login", ""),
                            "password": cred.get("Password", ""),
                            "url": cred.get("URL", "")
                        })
                        if module_name not in result["summary"]["by_module"]:
                            result["summary"]["by_module"][module_name] = 0
                        result["summary"]["by_module"][module_name] += 1
            
            result["summary"]["total"] = len(result["credentials"])
        except json.JSONDecodeError:
            result["credentials"] = [{"raw": output}]
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
