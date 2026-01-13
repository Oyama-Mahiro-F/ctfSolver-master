"""
Xray包装器 - 被动/主动扫描
"""
import os
import subprocess
import json
import time
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class XrayWrapper(ToolBase):
    """Xray工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="xray",
            description="被动/主动扫描工具，支持webhook推送"
        )
        self.required_params = ["target"]
        self.optional_params = ["proxy", "webhook", "scan_type", "plugins"]
        self.xray_path = get_tool_path("xray") or "xray"
        self.webhook_results = []  # 存储webhook接收的结果
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Xray扫描"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # URL
            proxy = params.get("proxy")
            webhook = params.get("webhook")  # webhook URL
            scan_type = params.get("scan_type", "webscan")  # webscan, reverse
            plugins = params.get("plugins")  # 插件列表
            
            # 构建Xray命令
            cmd = [self.xray_path]
            
            # 扫描类型
            if scan_type == "webscan":
                cmd.append("webscan")
            elif scan_type == "reverse":
                cmd.append("reverse")
            
            # 目标URL
            cmd.extend(["--url", target])
            
            # 代理
            if proxy:
                cmd.extend(["--proxy", proxy])
            
            # Webhook
            if webhook:
                cmd.extend(["--webhook-output", webhook])
            
            # 插件
            if plugins:
                if isinstance(plugins, list):
                    plugins_str = ",".join(plugins)
                else:
                    plugins_str = str(plugins)
                cmd.extend(["--plugins", plugins_str])
            
            # JSON输出文件
            import tempfile
            output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            output_file.close()
            cmd.extend(["--json-output", output_file.name])
            
            # 执行命令
            logger.info(f"执行Xray: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            # 读取JSON输出
            parsed_data = {}
            if os.path.exists(output_file.name):
                try:
                    with open(output_file.name, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        vulnerabilities = []
                        for line in lines:
                            if line.strip():
                                try:
                                    vuln_data = json.loads(line)
                                    vulnerabilities.append(vuln_data)
                                except json.JSONDecodeError:
                                    continue
                    parsed_data = self._parse_output(vulnerabilities)
                    os.unlink(output_file.name)
                except Exception as e:
                    logger.error(f"读取Xray输出失败: {e}")
                    if os.path.exists(output_file.name):
                        os.unlink(output_file.name)
            
            if result.returncode == 0 or parsed_data.get("vulnerabilities"):
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
                error="Xray执行超时"
            )
        except Exception as e:
            logger.error(f"Xray执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, vulnerabilities: list) -> Dict[str, Any]:
        """解析Xray输出"""
        result = {
            "vulnerabilities": [],
            "summary": {
                "total": len(vulnerabilities),
                "by_type": {},
                "by_severity": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "info": 0
                }
            }
        }
        
        for vuln in vulnerabilities:
            vuln_data = {
                "plugin": vuln.get("plugin", ""),
                "target": vuln.get("target", {}).get("url", ""),
                "detail": vuln.get("detail", {}),
                "severity": vuln.get("detail", {}).get("severity", "info"),
                "type": vuln.get("plugin", "").split("-")[0] if "-" in vuln.get("plugin", "") else vuln.get("plugin", "")
            }
            
            result["vulnerabilities"].append(vuln_data)
            
            # 统计
            vuln_type = vuln_data["type"]
            if vuln_type not in result["summary"]["by_type"]:
                result["summary"]["by_type"][vuln_type] = 0
            result["summary"]["by_type"][vuln_type] += 1
            
            severity = vuln_data["severity"].lower()
            if severity in result["summary"]["by_severity"]:
                result["summary"]["by_severity"][severity] += 1
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return {"raw_output": raw_output}
