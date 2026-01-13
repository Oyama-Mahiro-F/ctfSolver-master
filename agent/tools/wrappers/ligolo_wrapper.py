"""
Ligolo-ng包装器 - 新一代隧道工具
"""
import os
import subprocess
import asyncio
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class LigoloWrapper(ToolBase):
    """Ligolo-ng工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="ligolo",
            description="新一代隧道工具，支持TUN接口，比SOCKS更稳定"
        )
        self.required_params = ["mode"]
        self.optional_params = ["server_address", "listen_port", "local_port", "remote_port"]
        self.ligolo_path = get_tool_path("ligolo") or "ligolo-ng"
        self.active_tunnels: Dict[str, Any] = {}
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Ligolo隧道建立"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            mode = params["mode"]  # server或client
            server_address = params.get("server_address")
            listen_port = params.get("listen_port", 11601)
            local_port = params.get("local_port")
            remote_port = params.get("remote_port")
            
            if mode == "server":
                # 启动服务器
                cmd = [self.ligolo_path, "server", "-l", str(listen_port)]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                tunnel_id = f"ligolo_server_{int(asyncio.get_event_loop().time())}"
                self.active_tunnels[tunnel_id] = {
                    "process_id": process.pid,
                    "mode": mode,
                    "listen_port": listen_port
                }
                
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    data={
                        "tunnel_id": tunnel_id,
                        "mode": mode,
                        "process_id": process.pid,
                        "listen_port": listen_port,
                        "instruction": "等待客户端连接"
                    }
                )
            
            elif mode == "client":
                if not server_address:
                    return ToolResult(
                        status=ToolResultStatus.ERROR,
                        error="客户端模式需要server_address参数"
                    )
                
                # 启动客户端
                cmd = [self.ligolo_path, "client", "-s", server_address]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                tunnel_id = f"ligolo_client_{int(asyncio.get_event_loop().time())}"
                self.active_tunnels[tunnel_id] = {
                    "process_id": process.pid,
                    "mode": mode,
                    "server_address": server_address
                }
                
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    data={
                        "tunnel_id": tunnel_id,
                        "mode": mode,
                        "process_id": process.pid,
                        "server_address": server_address
                    }
                )
            
            else:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=f"不支持的模式: {mode}"
                )
        
        except Exception as e:
            logger.error(f"Ligolo执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return {"raw_output": raw_output}
