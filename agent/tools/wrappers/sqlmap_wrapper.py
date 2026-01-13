"""
SQLMap包装器 - SQL注入检测和利用
"""
import os
import subprocess
import json
import tempfile
import re
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path, get_tool_config


class SQLMapWrapper(ToolBase):
    """SQLMap工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="sqlmap",
            description="自动化SQL注入检测和利用工具"
        )
        self.required_params = ["target"]
        self.optional_params = ["method", "data", "cookie", "headers", "level", "risk", "batch"]
        self.sqlmap_path = get_tool_path("sqlmap") or "sqlmap"
        self.config = get_tool_config("sqlmap")
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行SQLMap扫描"""
        try:
            # 验证参数
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]
            method = params.get("method", "GET")
            data = params.get("data")
            cookie = params.get("cookie")
            headers = params.get("headers")
            level = params.get("level", self.config.get("level", 1))
            risk = params.get("risk", self.config.get("risk_level", 1))
            batch = params.get("batch", self.config.get("batch_mode", True))
            
            # 构建SQLMap命令
            cmd = [self.sqlmap_path]
            
            # 目标URL
            if method.upper() == "POST" and data:
                cmd.extend(["-u", target, "--data", data])
            else:
                cmd.extend(["-u", target])
            
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
            
            # 测试级别和风险级别
            cmd.extend(["--level", str(level)])
            cmd.extend(["--risk", str(risk)])
            
            # 批处理模式
            if batch:
                cmd.append("--batch")
            
            # 输出格式
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                output_file = tmp_file.name
                cmd.extend(["--output-dir", os.path.dirname(output_file)])
                
                # 执行命令
                logger.info(f"执行SQLMap: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30分钟超时
                )
                
                # 解析输出
                parsed_data = self._parse_output(result.stdout, result.stderr)
                
                # 清理临时文件
                if os.path.exists(output_file):
                    os.unlink(output_file)
                
                # SQLMap返回码0表示成功，但即使有注入也可能返回非0
                # 所以主要看输出内容
                if "injection" in result.stdout.lower() or parsed_data.get("injection_points"):
                    return ToolResult(
                        status=ToolResultStatus.SUCCESS,
                        data=parsed_data,
                        raw_output=result.stdout
                    )
                elif result.returncode == 0:
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
                error="SQLMap执行超时"
            )
        except Exception as e:
            logger.error(f"SQLMap执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析SQLMap输出"""
        result = {
            "injection_points": [],
            "database_info": {},
            "summary": {
                "vulnerable": False,
                "dbms": None,
                "technique": None
            }
        }
        
        # 检测是否有SQL注入
        if "sqlmap identified the following injection point" in stdout.lower():
            result["summary"]["vulnerable"] = True
            
            # 提取数据库类型
            dbms_match = re.search(r"back-end DBMS: (.+)", stdout, re.IGNORECASE)
            if dbms_match:
                result["summary"]["dbms"] = dbms_match.group(1).strip()
            
            # 提取注入技术
            technique_match = re.search(r"Parameter: (.+) \((.+)\)", stdout, re.IGNORECASE)
            if technique_match:
                param = technique_match.group(1)
                technique = technique_match.group(2)
                result["injection_points"].append({
                    "parameter": param,
                    "technique": technique
                })
                result["summary"]["technique"] = technique
            
            # 提取数据库信息
            db_info_match = re.search(r"Database: (.+)", stdout, re.IGNORECASE)
            if db_info_match:
                result["database_info"]["name"] = db_info_match.group(1).strip()
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output, "")
