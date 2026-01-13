"""
Masscan包装器 - 超高速端口扫描
"""
import os
import subprocess
import json
import re
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class MasscanWrapper(ToolBase):
    """Masscan工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="masscan",
            description="超高速端口扫描工具，适合大网段存活探测"
        )
        self.required_params = ["target"]
        self.optional_params = ["ports", "rate", "exclude"]
        self.masscan_path = get_tool_path("masscan") or "masscan"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Masscan扫描"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # IP地址或IP段
            ports = params.get("ports", "1-1000")
            rate = params.get("rate", 1000)  # 扫描速率（包/秒）
            exclude = params.get("exclude")
            
            # 构建Masscan命令
            cmd = [self.masscan_path]
            
            # 端口范围
            cmd.extend(["-p", str(ports)])
            
            # 扫描速率
            cmd.extend(["--rate", str(rate)])
            
            # 排除IP
            if exclude:
                cmd.extend(["--exclude", exclude])
            
            # JSON输出
            cmd.append("--json")
            
            # 添加目标
            cmd.append(target)
            
            # 执行命令
            logger.info(f"执行Masscan: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout)
            
            if result.returncode == 0 or parsed_data.get("hosts"):
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
                error="Masscan执行超时"
            )
        except Exception as e:
            logger.error(f"Masscan执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析Masscan JSON输出"""
        result = {
            "hosts": [],
            "summary": {
                "total_hosts": 0,
                "total_ports": 0
            }
        }
        
        # Masscan输出每行一个JSON对象
        hosts_dict = {}
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            try:
                entry = json.loads(line)
                if entry.get("ip"):
                    ip = entry["ip"]
                    port = entry.get("port", {}).get("port")
                    
                    if ip not in hosts_dict:
                        hosts_dict[ip] = {"ip": ip, "ports": []}
                    
                    if port:
                        hosts_dict[ip]["ports"].append({
                            "port": port,
                            "protocol": entry.get("port", {}).get("protocol", "tcp")
                        })
            except json.JSONDecodeError:
                continue
        
        result["hosts"] = list(hosts_dict.values())
        result["summary"]["total_hosts"] = len(result["hosts"])
        result["summary"]["total_ports"] = sum(len(h["ports"]) for h in result["hosts"])
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
