"""
Hydra包装器 - 在线密码爆破
"""
import os
import subprocess
import json
import re
from typing import Dict, Any, List
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class HydraWrapper(ToolBase):
    """Hydra工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="hydra",
            description="在线密码爆破工具（SSH, FTP, RDP, MySQL等）"
        )
        self.required_params = ["target", "service"]
        self.optional_params = ["username", "password", "username_list", "password_list", "threads"]
        self.hydra_path = get_tool_path("hydra") or "hydra"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Hydra爆破"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # IP地址或主机名
            service = params["service"]  # ssh, ftp, rdp, mysql等
            username = params.get("username")
            password = params.get("password")
            username_list = params.get("username_list")
            password_list = params.get("password_list")
            threads = params.get("threads", 16)
            
            # 构建Hydra命令
            cmd = [self.hydra_path]
            
            # 用户名
            if username:
                cmd.extend(["-l", username])
            elif username_list:
                cmd.extend(["-L", username_list])
            else:
                # 默认用户名列表
                cmd.extend(["-L", "/usr/share/wordlists/usernames.txt"])
            
            # 密码
            if password:
                cmd.extend(["-p", password])
            elif password_list:
                cmd.extend(["-P", password_list])
            else:
                # 默认密码列表
                cmd.extend(["-P", "/usr/share/wordlists/passwords.txt"])
            
            # 线程数
            cmd.extend(["-t", str(threads)])
            
            # 目标和服务
            cmd.extend([target, service])
            
            # 执行命令
            logger.info(f"执行Hydra: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout, result.stderr)
            
            if parsed_data.get("successful_logins"):
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
                error="Hydra执行超时"
            )
        except Exception as e:
            logger.error(f"Hydra执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析Hydra输出"""
        result = {
            "successful_logins": [],
            "summary": {
                "total_found": 0,
                "service": None
            }
        }
        
        # 提取成功登录
        import re
        # Hydra输出格式: [service] host:port login:password
        login_pattern = re.compile(r'\[(\w+)\]\s+host:\s*([^\s]+)\s+login:\s*([^\s]+)\s+password:\s*(.+)', re.IGNORECASE)
        matches = login_pattern.findall(stdout)
        
        for service, host, login, password in matches:
            result["successful_logins"].append({
                "service": service,
                "host": host,
                "username": login,
                "password": password
            })
            result["summary"]["service"] = service
        
        result["summary"]["total_found"] = len(result["successful_logins"])
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output, "")
