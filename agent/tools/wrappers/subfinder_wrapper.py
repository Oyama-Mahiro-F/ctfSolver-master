"""
Subfinder包装器 - 子域名收集
"""
import os
import subprocess
import json
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class SubfinderWrapper(ToolBase):
    """Subfinder工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="subfinder",
            description="子域名收集工具"
        )
        self.required_params = ["domain"]
        self.optional_params = ["silent", "all", "recursive"]
        self.subfinder_path = get_tool_path("subfinder") or "subfinder"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Subfinder扫描"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            domain = params["domain"]
            silent = params.get("silent", True)
            all_sources = params.get("all", False)
            recursive = params.get("recursive", False)
            
            # 构建Subfinder命令
            cmd = [self.subfinder_path]
            
            # 域名
            cmd.extend(["-d", domain])
            
            # 静默模式（只输出域名）
            if silent:
                cmd.append("-silent")
            
            # 使用所有源
            if all_sources:
                cmd.append("-all")
            
            # 递归搜索
            if recursive:
                cmd.append("-recursive")
            
            # JSON输出
            cmd.append("-json")
            
            # 执行命令
            logger.info(f"执行Subfinder: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout)
            
            if result.returncode == 0 or parsed_data.get("domains"):
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
                error="Subfinder执行超时"
            )
        except Exception as e:
            logger.error(f"Subfinder执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析Subfinder JSON输出"""
        result = {
            "domains": [],
            "summary": {
                "total": 0
            }
        }
        
        # Subfinder输出每行一个JSON对象或域名
        domains_set = set()
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            try:
                # 尝试解析JSON
                entry = json.loads(line)
                if "host" in entry:
                    domains_set.add(entry["host"])
            except json.JSONDecodeError:
                # 如果不是JSON，可能是纯域名
                if line and '.' in line:
                    domains_set.add(line)
        
        result["domains"] = sorted(list(domains_set))
        result["summary"]["total"] = len(result["domains"])
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
