"""
扫描Agent - 负责漏洞扫描和发现
"""
import asyncio
from typing import Dict, Any, List, Optional
from tools.registry import tool_registry
from tools.executor import tool_executor
from tools.wrappers.nuclei_wrapper import NucleiWrapper
from tools.wrappers.xray_wrapper import XrayWrapper
from tools.wrappers.searchsploit_wrapper import SearchSploitWrapper
from core.knowledge_base import SharedContext, ResultType
from utils.logger import logger


class ScannerAgent:
    """扫描Agent - 执行漏洞扫描任务"""
    
    def __init__(self, agent_id: str, shared_context: Optional[SharedContext] = None):
        """
        初始化扫描Agent
        
        Args:
            agent_id: Agent ID
            shared_context: 共享上下文
        """
        self.agent_id = agent_id
        self.agent_name = "ScannerAgent"
        self.shared_context = shared_context
        self.capabilities = ["scan", "vuln_detect", "nuclei_scan"]
        
        # 注册工具
        if not tool_registry.get_tool("nuclei"):
            tool_registry.register(NucleiWrapper())
        if not tool_registry.get_tool("xray"):
            tool_registry.register(XrayWrapper())
        if not tool_registry.get_tool("searchsploit"):
            tool_registry.register(SearchSploitWrapper())
    
    async def execute_scan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行扫描任务
        
        Args:
            params: 任务参数
                - target: 目标URL或IP
                - scan_type: 扫描类型 (nuclei, xray等)
                - options: 其他选项
        
        Returns:
            Dict: 扫描结果
        """
        target = params.get("target")
        scan_type = params.get("scan_type", "nuclei")
        
        if not target:
            return {"error": "缺少target参数"}
        
        logger.info(f"[{self.agent_name}] 开始扫描任务: {target}, 类型: {scan_type}")
        
        results = {}
        
        # Nuclei扫描
        if scan_type in ["nuclei", "all"]:
            nuclei_result = await self._nuclei_scan(target, params.get("nuclei_options", {}))
            results["nuclei"] = nuclei_result
            
            # 保存到共享上下文
            if self.shared_context and nuclei_result.get("vulnerabilities"):
                for vuln in nuclei_result.get("vulnerabilities", []):
                    self.shared_context.add(
                        entry_type=ResultType.VULN,
                        source=self.agent_id,
                        data=vuln,
                        tags=["nuclei", vuln.get("severity", "unknown"), target]
                    )
        
        # Xray扫描
        if scan_type in ["xray", "all"]:
            xray_result = await self._xray_scan(target, params.get("xray_options", {}))
            results["xray"] = xray_result
            
            if self.shared_context and xray_result.get("vulnerabilities"):
                for vuln in xray_result.get("vulnerabilities", []):
                    self.shared_context.add(
                        entry_type=ResultType.VULN,
                        source=self.agent_id,
                        data=vuln,
                        tags=["xray", vuln.get("severity", "unknown"), target]
                    )
        
        # SearchSploit查询
        if scan_type in ["searchsploit", "all"]:
            software_info = params.get("software_info", {})
            if software_info:
                searchsploit_result = await self._searchsploit_query(software_info, params.get("searchsploit_options", {}))
                results["searchsploit"] = searchsploit_result
        
        logger.info(f"[{self.agent_name}] 扫描任务完成: {target}")
        return results
    
    async def _nuclei_scan(self, target: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """执行Nuclei扫描"""
        try:
            nuclei_params = {
                "target": target,
                "templates": options.get("templates"),
                "severity": options.get("severity"),
                "rate_limit": options.get("rate_limit", 150),
                "timeout": options.get("timeout", 10)
            }
            
            result = tool_executor.execute("nuclei", nuclei_params)
            
            if result.status.value == "success":
                return result.data
            else:
                return {"error": result.error, "data": result.data}
        
        except Exception as e:
            logger.error(f"Nuclei扫描失败: {e}")
            return {"error": str(e)}
    
    async def _xray_scan(self, target: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """执行Xray扫描"""
        try:
            xray_params = {
                "target": target,
                "proxy": options.get("proxy"),
                "webhook": options.get("webhook"),
                "scan_type": options.get("scan_type", "webscan"),
                "plugins": options.get("plugins")
            }
            
            result = tool_executor.execute("xray", xray_params)
            
            if result.status.value == "success":
                return result.data
            else:
                return {"error": result.error, "data": result.data}
        
        except Exception as e:
            logger.error(f"Xray扫描失败: {e}")
            return {"error": str(e)}
    
    async def _searchsploit_query(self, software_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """执行SearchSploit查询"""
        try:
            query = software_info.get("name", "")
            if software_info.get("version"):
                query = f"{query} {software_info['version']}"
            
            searchsploit_params = {
                "query": query,
                "exact": options.get("exact", False),
                "case_sensitive": options.get("case_sensitive", False),
                "type": options.get("type")
            }
            
            result = tool_executor.execute("searchsploit", searchsploit_params)
            
            if result.status.value == "success":
                return result.data
            else:
                return {"error": result.error, "data": result.data}
        
        except Exception as e:
            logger.error(f"SearchSploit查询失败: {e}")
            return {"error": str(e)}
    
    def get_capabilities(self) -> List[str]:
        """获取Agent能力"""
        return self.capabilities
