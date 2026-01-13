"""
Impacket包装器 - Windows协议利用工具集
"""
import os
import subprocess
import json
from typing import Dict, Any, List
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class ImpacketWrapper(ToolBase):
    """Impacket工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="impacket",
            description="Windows协议利用工具集（psexec, smbexec, wmiexec等）"
        )
        self.required_params = ["tool", "target"]
        self.optional_params = ["username", "password", "hash", "command", "options"]
        self.python_path = get_tool_path("impacket") or "python"
        # Impacket工具通常在/usr/local/bin或/opt/impacket/scripts目录
        self.impacket_base = "/usr/local/bin"  # 可以根据实际情况修改
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Impacket工具"""
        try:
            # 验证参数
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            tool_name = params["tool"]  # psexec, smbexec, wmiexec, secretsdump等
            target = params["target"]  # IP地址或主机名
            username = params.get("username")
            password = params.get("password")
            hash_value = params.get("hash")  # NTLM hash
            command = params.get("command", "whoami")
            options = params.get("options", {})
            
            # 构建命令
            # Impacket工具格式: python script.py [options] target
            tool_script = self._get_tool_script(tool_name)
            if not tool_script:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=f"不支持的Impacket工具: {tool_name}"
                )
            
            cmd = [self.python_path, tool_script]
            
            # 添加认证参数
            if hash_value:
                cmd.extend(["-hashes", hash_value])
            elif username and password:
                cmd.extend(["-u", username, "-p", password])
            elif username:
                cmd.extend(["-u", username])
            
            # 添加其他选项
            for key, value in options.items():
                if isinstance(value, bool) and value:
                    cmd.append(f"-{key}")
                elif value:
                    cmd.extend([f"-{key}", str(value)])
            
            # 添加命令（对于需要命令的工具）
            if tool_name in ["psexec", "smbexec", "wmiexec"]:
                cmd.extend(["-c", command])
            
            # 添加目标
            cmd.append(target)
            
            # 执行命令
            logger.info(f"执行Impacket {tool_name}: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # 解析输出
            parsed_data = self._parse_output(tool_name, result.stdout, result.stderr)
            
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
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolResultStatus.TIMEOUT,
                error="Impacket执行超时"
            )
        except Exception as e:
            logger.error(f"Impacket执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _get_tool_script(self, tool_name: str) -> str:
        """获取工具脚本路径"""
        tool_mapping = {
            "psexec": "psexec.py",
            "smbexec": "smbexec.py",
            "wmiexec": "wmiexec.py",
            "secretsdump": "secretsdump.py",
            "smbclient": "smbclient.py",
            "getTGT": "getTGT.py",
            "getST": "getST.py",
        }
        
        script_name = tool_mapping.get(tool_name.lower())
        if not script_name:
            return None
        
        # 尝试多个可能的路径
        possible_paths = [
            os.path.join(self.impacket_base, script_name),
            os.path.join("/opt/impacket/examples", script_name),
            os.path.join("/usr/share/impacket/examples", script_name),
            script_name  # 如果在PATH中
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or os.system(f"which {script_name}") == 0:
                return path
        
        return script_name  # 返回脚本名，让系统尝试查找
    
    def _parse_output(self, tool_name: str, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析Impacket输出"""
        result = {
            "tool": tool_name,
            "output": stdout,
            "error": stderr,
            "success": len(stderr) == 0 or "error" not in stderr.lower()
        }
        
        # 根据工具类型解析特定信息
        if tool_name == "secretsdump":
            # 解析secretsdump的输出（包含哈希值）
            result["hashes"] = self._parse_secretsdump_output(stdout)
        elif tool_name in ["psexec", "smbexec", "wmiexec"]:
            # 解析命令执行结果
            result["command_output"] = stdout
        
        return result
    
    def _parse_secretsdump_output(self, output: str) -> List[Dict[str, str]]:
        """解析secretsdump输出中的哈希值"""
        hashes = []
        lines = output.split('\n')
        
        for line in lines:
            # 格式: username:rid:lmhash:nthash:::
            if ':::' in line and ':' in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    hashes.append({
                        "username": parts[0],
                        "rid": parts[1],
                        "lmhash": parts[2],
                        "nthash": parts[3]
                    })
        
        return hashes
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return {"raw_output": raw_output}
