"""
隧道Agent - 负责代理和隧道建立
"""
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
from tools.registry import tool_registry
from tools.executor import tool_executor
from tools.wrappers.ligolo_wrapper import LigoloWrapper
from tools.wrappers.proxychains_wrapper import ProxyChainsWrapper
from core.knowledge_base import SharedContext, ResultType
from utils.logger import logger


class TunnelAgent:
    """隧道Agent - 执行隧道建立任务"""
    
    def __init__(self, agent_id: str, shared_context: Optional[SharedContext] = None):
        """
        初始化隧道Agent
        
        Args:
            agent_id: Agent ID
            shared_context: 共享上下文
        """
        self.agent_id = agent_id
        self.agent_name = "TunnelAgent"
        self.shared_context = shared_context
        self.capabilities = ["tunnel", "proxy", "chisel", "frp", "ligolo", "proxychains"]
        self.active_tunnels: Dict[str, Dict[str, Any]] = {}
        
        # 注册工具
        if not tool_registry.get_tool("ligolo"):
            tool_registry.register(LigoloWrapper())
        if not tool_registry.get_tool("proxychains"):
            tool_registry.register(ProxyChainsWrapper())
    
    async def execute_tunnel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行隧道建立任务
        
        Args:
            params: 任务参数
                - tunnel_type: 隧道类型 (chisel, frp, ligolo等)
                - mode: 模式 (server, client)
                - server_address: 服务器地址
                - local_port: 本地端口
                - remote_port: 远程端口
                - options: 其他选项
        
        Returns:
            Dict: 隧道建立结果
        """
        tunnel_type = params.get("tunnel_type", "chisel")
        mode = params.get("mode", "client")
        
        logger.info(f"[{self.agent_name}] 开始建立隧道: {tunnel_type}, 模式: {mode}")
        
        results = {}
        
        # Chisel隧道
        if tunnel_type == "chisel":
            chisel_result = await self._chisel_tunnel(params)
            results["chisel"] = chisel_result
            
            if self.shared_context and chisel_result.get("success"):
                tunnel_id = chisel_result.get("tunnel_id")
                self.active_tunnels[tunnel_id] = chisel_result
                
                self.shared_context.add(
                    entry_type=ResultType.TUNNEL,
                    source=self.agent_id,
                    data=chisel_result,
                    tags=["chisel", mode]
                )
        
        # Frp隧道
        elif tunnel_type == "frp":
            frp_result = await self._frp_tunnel(params)
            results["frp"] = frp_result
            
            if self.shared_context and frp_result.get("success"):
                tunnel_id = frp_result.get("tunnel_id")
                self.active_tunnels[tunnel_id] = frp_result
                
                self.shared_context.add(
                    entry_type=ResultType.TUNNEL,
                    source=self.agent_id,
                    data=frp_result,
                    tags=["frp", mode]
                )
        
        # Ligolo-ng隧道
        elif tunnel_type == "ligolo":
            ligolo_result = await self._ligolo_tunnel(params)
            results["ligolo"] = ligolo_result
            
            if self.shared_context and ligolo_result.get("tunnel_id"):
                tunnel_id = ligolo_result.get("tunnel_id")
                self.active_tunnels[tunnel_id] = ligolo_result
                
                self.shared_context.add(
                    entry_type=ResultType.TUNNEL,
                    source=self.agent_id,
                    data=ligolo_result,
                    tags=["ligolo", params.get("mode", "client")]
                )
        
        logger.info(f"[{self.agent_name}] 隧道建立完成: {tunnel_type}")
        return results
    
    async def _chisel_tunnel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """建立Chisel隧道"""
        try:
            mode = params.get("mode", "client")
            server_address = params.get("server_address")
            local_port = params.get("local_port")
            remote_port = params.get("remote_port")
            
            if mode == "client":
                if not server_address:
                    return {"success": False, "error": "缺少server_address参数"}
                
                # 构建Chisel客户端命令
                cmd = ["chisel", "client", server_address, f"R:{local_port}:{remote_port}"]
                
                # 执行命令（后台运行）
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                tunnel_id = f"chisel_{int(asyncio.get_event_loop().time())}"
                
                return {
                    "success": True,
                    "tunnel_id": tunnel_id,
                    "tunnel_type": "chisel",
                    "mode": mode,
                    "process_id": process.pid,
                    "local_port": local_port,
                    "remote_port": remote_port,
                    "server_address": server_address
                }
            
            elif mode == "server":
                # 构建Chisel服务器命令
                listen_port = params.get("listen_port", 8080)
                cmd = ["chisel", "server", "--port", str(listen_port)]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                tunnel_id = f"chisel_server_{int(asyncio.get_event_loop().time())}"
                
                return {
                    "success": True,
                    "tunnel_id": tunnel_id,
                    "tunnel_type": "chisel",
                    "mode": mode,
                    "process_id": process.pid,
                    "listen_port": listen_port
                }
        
        except Exception as e:
            logger.error(f"Chisel隧道建立失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _frp_tunnel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """建立Frp隧道"""
        # 类似Chisel的实现
        logger.info("Frp隧道建立功能待实现")
        return {"success": False, "message": "Frp隧道功能待实现"}
    
    async def _ligolo_tunnel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """建立Ligolo-ng隧道"""
        try:
            ligolo_params = {
                "mode": params.get("mode", "client"),
                "server_address": params.get("server_address"),
                "listen_port": params.get("listen_port", 11601),
                "local_port": params.get("local_port"),
                "remote_port": params.get("remote_port")
            }
            
            result = tool_executor.execute("ligolo", ligolo_params)
            
            if result.status.value == "success":
                return result.data
            else:
                return {"error": result.error}
        
        except Exception as e:
            logger.error(f"Ligolo隧道建立失败: {e}")
            return {"error": str(e)}
    
    async def execute_proxychains(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """使用ProxyChains执行命令"""
        try:
            proxychains_params = {
                "command": params.get("command"),
                "proxy_config": params.get("proxy_config"),
                "proxy_type": params.get("proxy_type", "socks5"),
                "proxy_host": params.get("proxy_host", "127.0.0.1"),
                "proxy_port": params.get("proxy_port", 1080)
            }
            
            result = tool_executor.execute("proxychains", proxychains_params)
            
            if result.status.value == "success":
                return result.data
            else:
                return {"error": result.error}
        
        except Exception as e:
            logger.error(f"ProxyChains执行失败: {e}")
            return {"error": str(e)}
    
    def close_tunnel(self, tunnel_id: str) -> bool:
        """关闭隧道"""
        if tunnel_id in self.active_tunnels:
            tunnel_info = self.active_tunnels[tunnel_id]
            process_id = tunnel_info.get("process_id")
            
            if process_id:
                try:
                    import os
                    import signal
                    os.kill(process_id, signal.SIGTERM)
                    logger.info(f"关闭隧道: {tunnel_id}")
                    del self.active_tunnels[tunnel_id]
                    return True
                except Exception as e:
                    logger.error(f"关闭隧道失败: {e}")
                    return False
        
        return False
    
    def get_capabilities(self) -> List[str]:
        """获取Agent能力"""
        return self.capabilities
