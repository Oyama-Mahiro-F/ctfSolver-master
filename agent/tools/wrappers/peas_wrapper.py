"""
PEAS包装器 - 自动化提权信息收集
"""
import os
import subprocess
import re
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class PEASWrapper(ToolBase):
    """PEAS工具包装器（LinPEAS/WinPEAS）"""
    
    def __init__(self):
        super().__init__(
            name="peas",
            description="自动化提权信息收集工具（LinPEAS/WinPEAS）"
        )
        self.required_params = ["target", "os_type"]
        self.optional_params = ["credentials", "method"]
        self.peas_path = get_tool_path("peas") or "peas"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行PEAS扫描"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # IP地址
            os_type = params["os_type"]  # linux或windows
            credentials = params.get("credentials")
            method = params.get("method", "remote")  # remote或local
            
            # 选择PEAS脚本
            if os_type.lower() == "linux":
                peas_script = "linpeas.sh"
            elif os_type.lower() == "windows":
                peas_script = "winpeas.exe"
            else:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=f"不支持的OS类型: {os_type}"
                )
            
            # 如果是远程执行，需要通过SSH或其他方式
            # 这里简化处理，假设脚本已经在目标机器上
            if method == "remote":
                # 需要通过SSH执行
                # 这里返回一个需要手动执行的指令
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    data={
                        "instruction": f"需要在目标机器上执行 {peas_script}",
                        "script": peas_script,
                        "os_type": os_type
                    }
                )
            else:
                # 本地执行（如果脚本在本地）
                cmd = [peas_script]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800
                )
                
                parsed_data = self._parse_output(result.stdout)
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    data=parsed_data,
                    raw_output=result.stdout
                )
        
        except Exception as e:
            logger.error(f"PEAS执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析PEAS输出，提取关键信息"""
        result = {
            "critical_findings": [],
            "warnings": [],
            "summary": {
                "suid_files": [],
                "sudo_commands": [],
                "writable_files": [],
                "kernel_vulns": []
            }
        }
        
        # 提取关键信息（红色标记的内容）
        # PEAS使用ANSI颜色码标记重要信息
        red_pattern = re.compile(r'\x1b\[31m(.+?)\x1b\[0m', re.DOTALL)
        red_findings = red_pattern.findall(output)
        result["critical_findings"] = red_findings
        
        # 提取SUID文件
        suid_pattern = re.compile(r'SUID files:\s*(.+?)(?:\n\n|\Z)', re.DOTALL | re.IGNORECASE)
        suid_match = suid_pattern.search(output)
        if suid_match:
            result["summary"]["suid_files"] = [f.strip() for f in suid_match.group(1).split('\n') if f.strip()]
        
        # 提取sudo命令
        sudo_pattern = re.compile(r'sudo -l.*?\n(.+?)(?:\n\n|\Z)', re.DOTALL | re.IGNORECASE)
        sudo_match = sudo_pattern.search(output)
        if sudo_match:
            result["summary"]["sudo_commands"] = [c.strip() for c in sudo_match.group(1).split('\n') if c.strip()]
        
        # 提取内核漏洞
        kernel_pattern = re.compile(r'Kernel version.*?vulnerable.*?\n(.+?)(?:\n\n|\Z)', re.DOTALL | re.IGNORECASE)
        kernel_match = kernel_pattern.search(output)
        if kernel_match:
            result["summary"]["kernel_vulns"] = [v.strip() for v in kernel_match.group(1).split('\n') if v.strip()]
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
