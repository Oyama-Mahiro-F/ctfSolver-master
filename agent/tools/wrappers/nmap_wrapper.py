"""
Nmap包装器 - 端口扫描和服务识别
"""
import json
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from typing import Any, Dict

from config.penetration_config import get_tool_config, get_tool_path
from utils.logger import logger

from ..base import ToolBase, ToolResult, ToolResultStatus


class NmapWrapper(ToolBase):
    """Nmap工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="nmap",
            description="端口扫描和服务指纹识别工具"
        )
        self.required_params = ["target"]
        self.optional_params = ["ports", "scan_type", "service_version", "os_detection"]
        self.nmap_path = get_tool_path("nmap") or "nmap"
        self.config = get_tool_config("nmap")
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Nmap扫描"""
        try:
            # 验证参数
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]
            ports = params.get("ports", self.config.get("default_ports", "1-1000"))
            scan_type = params.get("scan_type", self.config.get("default_scan_type", "syn"))
            service_version = params.get("service_version", True)
            os_detection = params.get("os_detection", False)
            
            # 构建Nmap命令
            cmd = [self.nmap_path]
            
            # 扫描类型
            if scan_type == "syn":
                cmd.extend(["-sS"])
            elif scan_type == "tcp":
                cmd.extend(["-sT"])
            elif scan_type == "udp":
                cmd.extend(["-sU"])
            
            # 端口范围
            cmd.extend(["-p", str(ports)])
            
            # 服务版本检测
            if service_version:
                cmd.extend(["-sV"])
            
            # 操作系统检测
            if os_detection:
                cmd.extend(["-O"])
            
            # 输出格式（XML）
            output_format = self.config.get("output_format", "xml")
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp_file:
                output_file = tmp_file.name
                cmd.extend(["-oX", output_file])
                
                # 添加目标
                cmd.append(target)
                
                # 执行命令
                logger.info(f"执行Nmap: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10分钟超时
                )
                
                # 读取XML输出
                if os.path.exists(output_file):
                    try:
                        tree = ET.parse(output_file)
                        root = tree.getroot()
                        parsed_data = self._parse_xml_output(root)
                        
                        # 清理临时文件
                        os.unlink(output_file)
                        
                        if result.returncode == 0:
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
                    except Exception as e:
                        logger.error(f"解析Nmap XML输出失败: {e}")
                        os.unlink(output_file)
                        return ToolResult(
                            status=ToolResultStatus.ERROR,
                            error=f"解析输出失败: {str(e)}"
                        )
                else:
                    return ToolResult(
                        status=ToolResultStatus.ERROR,
                        error=f"Nmap执行失败: {result.stderr}"
                    )
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolResultStatus.TIMEOUT,
                error="Nmap执行超时"
            )
        except Exception as e:
            logger.error(f"Nmap执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_xml_output(self, root: ET.Element) -> Dict[str, Any]:
        """解析Nmap XML输出"""
        result = {
            "hosts": [],
            "summary": {
                "total_hosts": 0,
                "up_hosts": 0,
                "down_hosts": 0
            }
        }
        
        for host in root.findall("host"):
            host_data = {
                "address": None,
                "hostnames": [],
                "status": None,
                "ports": []
            }
            
            # 地址
            address_elem = host.find("address")
            if address_elem is not None:
                host_data["address"] = address_elem.get("addr")
                host_data["address_type"] = address_elem.get("addrtype")
            
            # 主机名
            hostnames_elem = host.find("hostnames")
            if hostnames_elem is not None:
                for hostname in hostnames_elem.findall("hostname"):
                    host_data["hostnames"].append({
                        "name": hostname.get("name"),
                        "type": hostname.get("type")
                    })
            
            # 状态
            status_elem = host.find("status")
            if status_elem is not None:
                host_data["status"] = status_elem.get("state")
            
            # 端口
            ports_elem = host.find("ports")
            if ports_elem is not None:
                for port in ports_elem.findall("port"):
                    port_data = {
                        "port": port.get("portid"),
                        "protocol": port.get("protocol"),
                        "state": None,
                        "service": None,
                        "version": None
                    }
                    
                    state_elem = port.find("state")
                    if state_elem is not None:
                        port_data["state"] = state_elem.get("state")
                    
                    service_elem = port.find("service")
                    if service_elem is not None:
                        port_data["service"] = service_elem.get("name")
                        port_data["version"] = service_elem.get("version")
                        port_data["product"] = service_elem.get("product")
                    
                    host_data["ports"].append(port_data)
            
            result["hosts"].append(host_data)
        
        # 更新摘要
        result["summary"]["total_hosts"] = len(result["hosts"])
        result["summary"]["up_hosts"] = sum(
            1 for h in result["hosts"] if h["status"] == "up"
        )
        result["summary"]["down_hosts"] = result["summary"]["total_hosts"] - result["summary"]["up_hosts"]
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出（备用方法）"""
        # 如果XML解析失败，可以尝试解析文本输出
        # 这里简化处理，实际应该实现文本解析逻辑
        return {"raw_output": raw_output}
