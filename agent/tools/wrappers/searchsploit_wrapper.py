"""
SearchSploit包装器 - Exploit-DB离线漏洞库查询
"""
import os
import subprocess
import re
from typing import Dict, Any, List
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class SearchSploitWrapper(ToolBase):
    """SearchSploit工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="searchsploit",
            description="Exploit-DB离线漏洞库查询工具"
        )
        self.required_params = ["query"]
        self.optional_params = ["exact", "case_sensitive", "type"]
        self.searchsploit_path = get_tool_path("searchsploit") or "searchsploit"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行SearchSploit查询"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            query = params["query"]  # 软件名称或CVE编号
            exact = params.get("exact", False)
            case_sensitive = params.get("case_sensitive", False)
            exploit_type = params.get("type")  # webapps, remote, local, dos等
            
            # 构建SearchSploit命令
            cmd = [self.searchsploit_path]
            
            # 精确匹配
            if exact:
                cmd.append("--exact")
            
            # 大小写敏感
            if case_sensitive:
                cmd.append("--case-sensitive")
            
            # 类型过滤
            if exploit_type:
                cmd.extend(["-t", exploit_type])
            
            # JSON输出
            cmd.append("--json")
            
            # 查询字符串
            cmd.append(query)
            
            # 执行命令
            logger.info(f"执行SearchSploit: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout)
            
            if result.returncode == 0 or parsed_data.get("exploits"):
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
                error="SearchSploit执行超时"
            )
        except Exception as e:
            logger.error(f"SearchSploit执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析SearchSploit输出"""
        result = {
            "exploits": [],
            "summary": {
                "total": 0,
                "by_type": {}
            }
        }
        
        try:
            import json
            # SearchSploit JSON输出
            data = json.loads(output)
            
            for exploit in data.get("RESULTS_EXPLOIT", []):
                exploit_data = {
                    "id": exploit.get("ID", ""),
                    "title": exploit.get("Title", ""),
                    "date_published": exploit.get("Date_Published", ""),
                    "author": exploit.get("Author", ""),
                    "type": exploit.get("Type", ""),
                    "platform": exploit.get("Platform", ""),
                    "edb_id": exploit.get("EDB-ID", ""),
                    "file_path": exploit.get("Path", "")
                }
                
                result["exploits"].append(exploit_data)
                
                # 统计
                exploit_type = exploit_data["type"]
                if exploit_type not in result["summary"]["by_type"]:
                    result["summary"]["by_type"][exploit_type] = 0
                result["summary"]["by_type"][exploit_type] += 1
            
            result["summary"]["total"] = len(result["exploits"])
        
        except (json.JSONDecodeError, ImportError):
            # 如果不是JSON，解析文本输出
            lines = output.split('\n')
            for line in lines:
                # 格式: Exploit ID | Title | Date | Author | Type | Platform
                if '|' in line and not line.startswith('-'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 6:
                        result["exploits"].append({
                            "id": parts[0],
                            "title": parts[1],
                            "date_published": parts[2],
                            "author": parts[3],
                            "type": parts[4],
                            "platform": parts[5]
                        })
            
            result["summary"]["total"] = len(result["exploits"])
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
