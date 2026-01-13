"""
FFuf包装器 - 目录和文件模糊测试
"""
import os
import subprocess
import json
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class FFufWrapper(ToolBase):
    """FFuf工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="ffuf",
            description="目录和文件模糊测试工具"
        )
        self.required_params = ["target", "wordlist"]
        self.optional_params = ["extensions", "recursion", "status_codes", "method"]
        self.ffuf_path = get_tool_path("ffuf") or "ffuf"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行FFuf扫描"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # URL，如 http://example.com/FUZZ
            wordlist = params["wordlist"]  # 字典文件路径
            extensions = params.get("extensions")  # 扩展名列表，如 ["php", "html"]
            recursion = params.get("recursion", False)
            status_codes = params.get("status_codes", "200,204,301,302,307,401,403")
            method = params.get("method", "GET")
            
            # 构建FFuf命令
            cmd = [self.ffuf_path]
            
            # URL（FUZZ是占位符）
            if "FUZZ" not in target:
                target = target.rstrip('/') + "/FUZZ"
            cmd.extend(["-u", target])
            
            # 字典
            cmd.extend(["-w", wordlist])
            
            # 扩展名
            if extensions:
                if isinstance(extensions, list):
                    extensions_str = ",".join(extensions)
                else:
                    extensions_str = str(extensions)
                cmd.extend(["-e", extensions_str])
            
            # 递归
            if recursion:
                cmd.append("-recursion")
            
            # 状态码
            cmd.extend(["-mc", status_codes])
            
            # HTTP方法
            cmd.extend(["-X", method])
            
            # JSON输出
            cmd.append("-json")
            
            # 执行命令
            logger.info(f"执行FFuf: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout)
            
            if result.returncode == 0 or parsed_data.get("results"):
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
                error="FFuf执行超时"
            )
        except Exception as e:
            logger.error(f"FFuf执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析FFuf JSON输出"""
        result = {
            "results": [],
            "summary": {
                "total_requests": 0,
                "total_results": 0,
                "status_codes": {}
            }
        }
        
        try:
            # FFuf输出JSON格式
            data = json.loads(output)
            
            # 解析结果
            for entry in data.get("results", []):
                result_entry = {
                    "url": entry.get("url", ""),
                    "status": entry.get("status", 0),
                    "length": entry.get("length", 0),
                    "words": entry.get("words", 0),
                    "lines": entry.get("lines", 0),
                    "content_type": entry.get("content-type", ""),
                    "redirect_location": entry.get("redirectlocation", "")
                }
                result["results"].append(result_entry)
                
                # 统计状态码
                status = result_entry["status"]
                if status not in result["summary"]["status_codes"]:
                    result["summary"]["status_codes"][status] = 0
                result["summary"]["status_codes"][status] += 1
            
            result["summary"]["total_requests"] = data.get("config", {}).get("total", 0)
            result["summary"]["total_results"] = len(result["results"])
        
        except json.JSONDecodeError:
            # 如果不是JSON，尝试解析文本输出
            result["results"] = [{"raw": output}]
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
