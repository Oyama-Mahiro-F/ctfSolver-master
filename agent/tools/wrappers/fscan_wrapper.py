"""
Fscan包装器 - 内网综合扫描工具
"""
import os
import subprocess
import re
import json
from typing import Dict, Any, List
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path, get_tool_config


class FscanWrapper(ToolBase):
    """Fscan工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="fscan",
            description="内网综合扫描工具，支持弱口令、漏洞扫描等"
        )
        self.required_params = ["target"]
        self.optional_params = ["threads", "timeout", "scan_type"]
        self.fscan_path = get_tool_path("fscan") or "fscan"
        self.config = get_tool_config("fscan")
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Fscan扫描"""
        try:
            # 验证参数
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # IP地址或IP段，如 "192.168.1.1" 或 "192.168.1.1/24"
            threads = params.get("threads", self.config.get("threads", 600))
            timeout = params.get("timeout", self.config.get("timeout", 3))
            scan_type = params.get("scan_type", "all")  # all, port, vuln, weakpass
            
            # 构建Fscan命令
            cmd = [self.fscan_path]
            
            # 目标
            cmd.extend(["-h", target])
            
            # 线程数
            cmd.extend(["-t", str(threads)])
            
            # 超时
            cmd.extend(["-time", str(timeout)])
            
            # 扫描类型
            if scan_type == "port":
                cmd.append("-np")  # 只扫描端口
            elif scan_type == "vuln":
                cmd.append("-no")  # 不扫描弱口令
            elif scan_type == "weakpass":
                cmd.append("-pw")  # 只扫描弱口令
            
            # 执行命令
            logger.info(f"执行Fscan: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
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
                error="Fscan执行超时"
            )
        except Exception as e:
            logger.error(f"Fscan执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析Fscan输出"""
        result = {
            "hosts": [],
            "ports": [],
            "vulnerabilities": [],
            "weak_passwords": [],
            "summary": {
                "total_hosts": 0,
                "total_ports": 0,
                "total_vulns": 0,
                "total_weakpass": 0
            }
        }
        
        lines = output.split('\n')
        current_host = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 解析主机信息
            host_match = re.match(r'(\d+\.\d+\.\d+\.\d+)', line)
            if host_match:
                ip = host_match.group(1)
                current_host = {
                    "ip": ip,
                    "ports": [],
                    "vulns": [],
                    "weakpass": []
                }
                result["hosts"].append(current_host)
                continue
            
            # 解析端口信息 (格式: 192.168.1.1:22 open)
            port_match = re.match(r'(\d+\.\d+\.\d+\.\d+):(\d+)\s+(open|closed)', line)
            if port_match:
                ip = port_match.group(1)
                port = port_match.group(2)
                status = port_match.group(3)
                
                port_info = {
                    "ip": ip,
                    "port": int(port),
                    "status": status
                }
                result["ports"].append(port_info)
                
                if current_host and current_host["ip"] == ip:
                    current_host["ports"].append(port_info)
                continue
            
            # 解析漏洞信息 (格式: [*] 192.168.1.1 MS17-010)
            vuln_match = re.match(r'\[\*\]\s+(\d+\.\d+\.\d+\.\d+)\s+(.+)', line)
            if vuln_match:
                ip = vuln_match.group(1)
                vuln_name = vuln_match.group(2)
                
                vuln_info = {
                    "ip": ip,
                    "name": vuln_name
                }
                result["vulnerabilities"].append(vuln_info)
                
                if current_host and current_host["ip"] == ip:
                    current_host["vulns"].append(vuln_info)
                continue
            
            # 解析弱口令信息 (格式: [*] 192.168.1.1:3306 mysql root:123456)
            weakpass_match = re.match(r'\[\*\]\s+(\d+\.\d+\.\d+\.\d+):(\d+)\s+(\w+)\s+(\w+):(.+)', line)
            if weakpass_match:
                ip = weakpass_match.group(1)
                port = weakpass_match.group(2)
                service = weakpass_match.group(3)
                username = weakpass_match.group(4)
                password = weakpass_match.group(5)
                
                weakpass_info = {
                    "ip": ip,
                    "port": int(port),
                    "service": service,
                    "username": username,
                    "password": password
                }
                result["weak_passwords"].append(weakpass_info)
                
                if current_host and current_host["ip"] == ip:
                    current_host["weakpass"].append(weakpass_info)
                continue
        
        # 更新摘要
        result["summary"]["total_hosts"] = len(result["hosts"])
        result["summary"]["total_ports"] = len(result["ports"])
        result["summary"]["total_vulns"] = len(result["vulnerabilities"])
        result["summary"]["total_weakpass"] = len(result["weak_passwords"])
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
