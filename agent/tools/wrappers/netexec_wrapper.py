"""
NetExec包装器 - 域环境自动化渗透
"""
import os
import subprocess
import json
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class NetExecWrapper(ToolBase):
    """NetExec工具包装器（原CrackMapExec）"""
    
    def __init__(self):
        super().__init__(
            name="netexec",
            description="域环境下的自动化渗透工具（喷洒密码、枚举共享等）"
        )
        self.required_params = ["target"]
        self.optional_params = ["username", "password", "hash", "action", "shares"]
        self.netexec_path = get_tool_path("netexec") or "netexec"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行NetExec"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # IP地址或IP段
            username = params.get("username")
            password = params.get("password")
            hash_value = params.get("hash")
            action = params.get("action", "smb")  # smb, ssh, winrm等
            shares = params.get("shares", False)
            
            # 构建NetExec命令
            cmd = [self.netexec_path, action, target]
            
            # 认证
            if hash_value:
                cmd.extend(["-H", hash_value])
            elif username and password:
                cmd.extend(["-u", username, "-p", password])
            elif username:
                cmd.extend(["-u", username])
            
            # 枚举共享
            if shares:
                cmd.append("--shares")
            
            # JSON输出
            cmd.append("--json")
            
            # 执行命令
            logger.info(f"执行NetExec: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout)
            
            if result.returncode == 0 or parsed_data.get("results"):
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
                error="NetExec执行超时"
            )
        except Exception as e:
            logger.error(f"NetExec执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析NetExec JSON输出"""
        result = {
            "results": [],
            "summary": {
                "total_hosts": 0,
                "successful_logins": 0
            }
        }
        
        try:
            data = json.loads(output)
            if isinstance(data, list):
                for entry in data:
                    result["results"].append(entry)
            elif isinstance(data, dict):
                result["results"].append(data)
            
            result["summary"]["total_hosts"] = len(result["results"])
            result["summary"]["successful_logins"] = sum(
                1 for r in result["results"] if r.get("status") == "success"
            )
        except json.JSONDecodeError:
            result["results"] = [{"raw": output}]
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
