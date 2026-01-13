"""
Commix包装器 - 自动化命令注入利用
"""
import os
import subprocess
import json
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class CommixWrapper(ToolBase):
    """Commix工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="commix",
            description="自动化命令注入检测和利用工具"
        )
        self.required_params = ["target"]
        self.optional_params = ["data", "cookie", "headers", "os_cmd", "batch"]
        self.commix_path = get_tool_path("commix") or "commix"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Commix扫描"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # URL
            data = params.get("data")
            cookie = params.get("cookie")
            headers = params.get("headers")
            os_cmd = params.get("os_cmd", "whoami")
            batch = params.get("batch", True)
            
            # 构建Commix命令
            cmd = [self.commix_path]
            
            # 目标URL
            cmd.extend(["-u", target])
            
            # POST数据
            if data:
                cmd.extend(["--data", data])
            
            # Cookie
            if cookie:
                cmd.extend(["--cookie", cookie])
            
            # Headers
            if headers:
                if isinstance(headers, dict):
                    for key, value in headers.items():
                        cmd.extend(["--headers", f"{key}: {value}"])
                elif isinstance(headers, str):
                    cmd.extend(["--headers", headers])
            
            # 操作系统命令
            cmd.extend(["--os-cmd", os_cmd])
            
            # 批处理模式
            if batch:
                cmd.append("--batch")
            
            # 执行命令
            logger.info(f"执行Commix: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout, result.stderr)
            
            if "injection" in result.stdout.lower() or parsed_data.get("vulnerable"):
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
                error="Commix执行超时"
            )
        except Exception as e:
            logger.error(f"Commix执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析Commix输出"""
        result = {
            "vulnerable": False,
            "injection_point": None,
            "os_type": None,
            "command_output": None,
            "technique": None
        }
        
        # 检测命令注入
        if "command injection" in stdout.lower() or "vulnerable" in stdout.lower():
            result["vulnerable"] = True
            
            # 提取注入点
            import re
            injection_match = re.search(r"Parameter '(.+?)' seems to be vulnerable", stdout, re.IGNORECASE)
            if injection_match:
                result["injection_point"] = injection_match.group(1)
            
            # 提取操作系统类型
            if "linux" in stdout.lower():
                result["os_type"] = "linux"
            elif "windows" in stdout.lower():
                result["os_type"] = "windows"
            
            # 提取命令输出
            output_match = re.search(r"Command output: (.+)", stdout, re.IGNORECASE | re.DOTALL)
            if output_match:
                result["command_output"] = output_match.group(1).strip()
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output, "")
