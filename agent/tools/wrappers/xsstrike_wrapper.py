"""
XSStrike包装器 - 高级XSS检测
"""
import os
import subprocess
import json
import re
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class XSStrikeWrapper(ToolBase):
    """XSStrike工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="xsstrike",
            description="高级XSS检测工具"
        )
        self.required_params = ["target"]
        self.optional_params = ["data", "cookie", "headers", "crawl", "threads"]
        self.xsstrike_path = get_tool_path("xsstrike") or "xsstrike"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行XSStrike扫描"""
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
            crawl = params.get("crawl", False)
            threads = params.get("threads", 30)
            
            # 构建XSStrike命令
            cmd = [self.xsstrike_path]
            
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
            
            # 爬取模式
            if crawl:
                cmd.append("--crawl")
            
            # 线程数
            cmd.extend(["-t", str(threads)])
            
            # 执行命令
            logger.info(f"执行XSStrike: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout, result.stderr)
            
            if "vulnerable" in result.stdout.lower() or parsed_data.get("vulnerable"):
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
                error="XSStrike执行超时"
            )
        except Exception as e:
            logger.error(f"XSStrike执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析XSStrike输出"""
        result = {
            "vulnerable": False,
            "xss_points": [],
            "payloads": [],
            "summary": {
                "total_found": 0
            }
        }
        
        # 检测XSS漏洞
        if "vulnerable" in stdout.lower() or "xss" in stdout.lower():
            result["vulnerable"] = True
            
            # 提取XSS点
            import re
            xss_pattern = re.compile(r"Parameter '(.+?)' is vulnerable.*?Payload: (.+?)", re.IGNORECASE | re.DOTALL)
            matches = xss_pattern.findall(stdout)
            
            for param, payload in matches:
                result["xss_points"].append({
                    "parameter": param.strip(),
                    "payload": payload.strip()
                })
                result["payloads"].append(payload.strip())
            
            result["summary"]["total_found"] = len(result["xss_points"])
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output, "")
