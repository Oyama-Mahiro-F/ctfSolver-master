"""
Nuclei包装器 - 基于模板的漏洞扫描
"""
import os
import subprocess
import json
import tempfile
from typing import Dict, Any, List
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path, get_tool_config


class NucleiWrapper(ToolBase):
    """Nuclei工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="nuclei",
            description="基于模板的漏洞扫描工具"
        )
        self.required_params = ["target"]
        self.optional_params = ["templates", "severity", "rate_limit", "timeout"]
        self.nuclei_path = get_tool_path("nuclei") or "nuclei"
        self.config = get_tool_config("nuclei")
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Nuclei扫描"""
        try:
            # 验证参数
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]
            templates = params.get("templates", self.config.get("template_path"))
            severity = params.get("severity")  # critical, high, medium, low, info
            rate_limit = params.get("rate_limit", self.config.get("rate_limit", 150))
            timeout = params.get("timeout", self.config.get("timeout", 10))
            
            # 构建Nuclei命令
            cmd = [self.nuclei_path]
            
            # 目标
            cmd.extend(["-u", target] if target.startswith("http") else ["-target", target])
            
            # 模板
            if templates:
                cmd.extend(["-t", templates])
            
            # 严重程度过滤
            if severity:
                cmd.extend(["-severity", severity])
            
            # 速率限制
            cmd.extend(["-rate-limit", str(rate_limit)])
            
            # 超时
            cmd.extend(["-timeout", str(timeout)])
            
            # JSON输出
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                output_file = tmp_file.name
                cmd.extend(["-json", "-o", output_file])
                
                # 执行命令
                logger.info(f"执行Nuclei: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                # 读取JSON输出
                if os.path.exists(output_file):
                    try:
                        with open(output_file, 'r', encoding='utf-8') as f:
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
                        
                        # 清理临时文件
                        os.unlink(output_file)
                        
                        if result.returncode == 0 or vulnerabilities:
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
                        logger.error(f"解析Nuclei输出失败: {e}")
                        if os.path.exists(output_file):
                            os.unlink(output_file)
                        return ToolResult(
                            status=ToolResultStatus.ERROR,
                            error=f"解析输出失败: {str(e)}"
                        )
                else:
                    return ToolResult(
                        status=ToolResultStatus.ERROR,
                        error=f"Nuclei执行失败: {result.stderr}"
                    )
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolResultStatus.TIMEOUT,
                error="Nuclei执行超时"
            )
        except Exception as e:
            logger.error(f"Nuclei执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, vulnerabilities: List[Dict]) -> Dict[str, Any]:
        """解析Nuclei输出"""
        result = {
            "vulnerabilities": [],
            "summary": {
                "total": len(vulnerabilities),
                "by_severity": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "info": 0
                },
                "by_type": {}
            }
        }
        
        for vuln in vulnerabilities:
            vuln_data = {
                "template_id": vuln.get("template-id", ""),
                "name": vuln.get("name", ""),
                "severity": vuln.get("info", {}).get("severity", "unknown"),
                "target": vuln.get("host", ""),
                "matched_at": vuln.get("matched-at", ""),
                "description": vuln.get("info", {}).get("description", ""),
                "reference": vuln.get("info", {}).get("reference", []),
                "tags": vuln.get("info", {}).get("tags", [])
            }
            
            result["vulnerabilities"].append(vuln_data)
            
            # 统计
            severity = vuln_data["severity"].lower()
            if severity in result["summary"]["by_severity"]:
                result["summary"]["by_severity"][severity] += 1
            
            vuln_type = vuln_data["template_id"]
            if vuln_type not in result["summary"]["by_type"]:
                result["summary"]["by_type"][vuln_type] = 0
            result["summary"]["by_type"][vuln_type] += 1
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return {"raw_output": raw_output}
