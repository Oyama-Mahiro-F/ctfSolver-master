"""
侦察Agent - 负责信息收集和资产发现
"""
import asyncio
from typing import Any, Dict, List, Optional

from core.knowledge_base import ResultType, SharedContext
from tools.executor import tool_executor
from tools.registry import tool_registry
from tools.wrappers.ffuf_wrapper import FFufWrapper
from tools.wrappers.masscan_wrapper import MasscanWrapper
from tools.wrappers.nmap_wrapper import NmapWrapper
from tools.wrappers.subfinder_wrapper import SubfinderWrapper
from tools.wrappers.whatweb_wrapper import WhatWebWrapper
from utils.logger import logger


class ReconAgent:
    """侦察Agent - 执行信息收集任务"""
    
    def __init__(self, agent_id: str, shared_context: Optional[SharedContext] = None):
        """
        初始化侦察Agent
        
        Args:
            agent_id: Agent ID
            shared_context: 共享上下文
        """
        self.agent_id = agent_id
        self.agent_name = "ReconAgent"
        self.shared_context = shared_context
        self.capabilities = ["recon", "port_scan", "subdomain_enum", "web_fingerprint"]
        
        # 注册工具
        if not tool_registry.get_tool("nmap"):
            tool_registry.register(NmapWrapper())
        if not tool_registry.get_tool("masscan"):
            tool_registry.register(MasscanWrapper())
        if not tool_registry.get_tool("subfinder"):
            tool_registry.register(SubfinderWrapper())
        if not tool_registry.get_tool("whatweb"):
            tool_registry.register(WhatWebWrapper())
        if not tool_registry.get_tool("ffuf"):
            tool_registry.register(FFufWrapper())
    
    async def execute_recon(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行侦察任务
        
        Args:
            params: 任务参数
                - target: 目标IP或域名
                - scan_type: 扫描类型 (port_scan, subdomain, fingerprint等)
                - options: 其他选项
        
        Returns:
            Dict: 侦察结果
        """
        target = params.get("target")
        scan_type = params.get("scan_type", "port_scan")
        
        if not target:
            return {"error": "缺少target参数"}
        
        logger.info(f"[{self.agent_name}] 开始侦察任务: {target}, 类型: {scan_type}")
        
        results = {}
        
        # 端口扫描
        if scan_type in ["port_scan", "all"]:
            port_result = await self._port_scan(target, params.get("port_scan_options", {}))
            results["port_scan"] = port_result
            
            # 保存到共享上下文
            if self.shared_context and port_result.get("hosts"):
                self.shared_context.add(
                    entry_type=ResultType.RECON,
                    source=self.agent_id,
                    data=port_result,
                    tags=["port_scan", target]
                )
        
        # 子域名枚举
        if scan_type in ["subdomain", "all"]:
            subdomain_result = await self._subdomain_enum(target, params.get("subdomain_options", {}))
            results["subdomain"] = subdomain_result
            
            if self.shared_context and subdomain_result.get("domains"):
                self.shared_context.add(
                    entry_type=ResultType.RECON,
                    source=self.agent_id,
                    data=subdomain_result,
                    tags=["subdomain", target]
                )
        
        # Web指纹识别
        if scan_type in ["fingerprint", "all"]:
            fingerprint_result = await self._web_fingerprint(target, params.get("fingerprint_options", {}))
            results["fingerprint"] = fingerprint_result
            
            if self.shared_context and fingerprint_result.get("technologies"):
                self.shared_context.add(
                    entry_type=ResultType.RECON,
                    source=self.agent_id,
                    data=fingerprint_result,
                    tags=["fingerprint", target]
                )
        
        logger.info(f"[{self.agent_name}] 侦察任务完成: {target}")
        return results
    
    async def _port_scan(self, target: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """执行端口扫描"""
        try:
            nmap_params = {
                "target": target,
                "ports": options.get("ports", "1-1000"),
                "scan_type": options.get("scan_type", "syn"),
                "service_version": options.get("service_version", True),
                "os_detection": options.get("os_detection", False)
            }
            
            result = tool_executor.execute("nmap", nmap_params)
            
            if result.status.value == "success":
                return result.data
            else:
                return {"error": result.error, "data": result.data}
        
        except Exception as e:
            logger.error(f"端口扫描失败: {e}")
            return {"error": str(e)}
    
    async def _subdomain_enum(self, target: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """执行子域名枚举"""
        try:
            subfinder_params = {
                "domain": target,
                "silent": options.get("silent", True),
                "all": options.get("all", False),
                "recursive": options.get("recursive", False)
            }
            
            result = tool_executor.execute("subfinder", subfinder_params)
            
            if result.status.value == "success":
                return result.data
            else:
                return {"error": result.error, "data": result.data}
        
        except Exception as e:
            logger.error(f"子域名枚举失败: {e}")
            return {"error": str(e)}
    
    async def _web_fingerprint(self, target: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """执行Web指纹识别"""
        try:
            whatweb_params = {
                "target": target,
                "aggression": options.get("aggression", 1),
                "verbosity": options.get("verbosity", 0)
            }
            
            result = tool_executor.execute("whatweb", whatweb_params)
            
            if result.status.value == "success":
                return result.data
            else:
                return {"error": result.error, "data": result.data}
        
        except Exception as e:
            logger.error(f"Web指纹识别失败: {e}")
            return {"error": str(e)}
    
    def get_capabilities(self) -> List[str]:
        """获取Agent能力"""
        return self.capabilities
