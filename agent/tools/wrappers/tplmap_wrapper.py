"""
Tplmap包装器 - 服务端模板注入检测与利用
"""
import os
import subprocess
import json
import re
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class TplmapWrapper(ToolBase):
    """Tplmap工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="tplmap",
            description="服务端模板注入(SSTI)检测与利用工具"
        )
        self.required_params = ["target"]
        self.optional_params = ["data", "cookie", "engine", "os_cmd"]
        self.tplmap_path = get_tool_path("tplmap") or "tplmap"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Tplmap扫描"""
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
            engine = params.get("engine")  # jinja2, mako, freemarker等
            os_cmd = params.get("os_cmd", "whoami")
            
            # 构建Tplmap命令
            cmd = [self.tplmap_path]
            
            # 目标URL
            cmd.extend(["-u", target])
            
            # POST数据
            if data:
                cmd.extend(["--data", data])
            
            # Cookie
            if cookie:
                cmd.extend(["--cookie", cookie])
            
            # 模板引擎
            if engine:
                cmd.extend(["--engine", engine])
            
            # 操作系统命令
            cmd.extend(["--os-cmd", os_cmd])
            
            # 执行命令
            logger.info(f"执行Tplmap: {' '.join(cmd)}")
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
                error="Tplmap执行超时"
            )
        except Exception as e:
            logger.error(f"Tplmap执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析Tplmap输出"""
        result = {
            "vulnerable": False,
            "injection_point": None,
            "engine": None,
            "command_output": None,
            "payload": None
        }
        
        # 检测SSTI
        if "template injection" in stdout.lower() or "vulnerable" in stdout.lower():
            result["vulnerable"] = True
            
            # 提取模板引擎
            engine_match = re.search(r"Engine: (.+)", stdout, re.IGNORECASE)
            if engine_match:
                result["engine"] = engine_match.group(1).strip()
            
            # 提取注入点
            param_match = re.search(r"Parameter '(.+?)' seems to be vulnerable", stdout, re.IGNORECASE)
            if param_match:
                result["injection_point"] = param_match.group(1)
            
            # 提取命令输出
            output_match = re.search(r"Command output: (.+)", stdout, re.IGNORECASE | re.DOTALL)
            if output_match:
                result["command_output"] = output_match.group(1).strip()
            
            # 提取payload
            payload_match = re.search(r"Payload: (.+)", stdout, re.IGNORECASE)
            if payload_match:
                result["payload"] = payload_match.group(1).strip()
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output, "")
