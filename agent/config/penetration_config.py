"""
渗透测试配置 - 工具路径、Docker配置、AI模型配置等
"""
import os
from typing import Any, Dict, Optional

# 工具路径配置
TOOL_PATHS = {
    # 第一阶段：信息收集与资产侦察
    "nmap": "nmap",
    "masscan": "masscan",
    "rustscan": "rustscan",
    "subfinder": "subfinder",
    "oneforall": "oneforall",
    "whatweb": "whatweb",
    "wappalyzer": "wappalyzer",
    "ffuf": "ffuf",
    "dirsearch": "dirsearch",
    
    # 第二阶段：漏洞扫描与发现
    "nuclei": "nuclei",
    "xray": "xray",
    "goby": "goby",
    "searchsploit": "searchsploit",
    
    # 第三阶段：Web专项攻击
    "sqlmap": "sqlmap",
    "commix": "commix",
    "tplmap": "tplmap",
    "xsstrike": "xsstrike",
    "hydra": "hydra",
    "medusa": "medusa",
    
    # 第四阶段：漏洞利用与权限获取
    "metasploit": "msfconsole",
    "msfrpc": "msfrpcd",
    "pocsuite3": "pocsuite3",
    
    # 第五阶段：后渗透与提权
    "peas": "peas",  # LinPEAS/WinPEAS
    "mimikatz": "mimikatz.exe",
    "lazagne": "laZagne",
    
    # 第六阶段：内网横向移动
    "fscan": "fscan",
    "impacket": "python",
    "netexec": "netexec",
    "bloodhound": "bloodhound",
    
    # 第七阶段：代理与隧道
    "chisel": "chisel",
    "frp": "frpc",
    "ligolo": "ligolo-ng",
    "proxychains": "proxychains",
}

# Docker配置
DOCKER_CONFIG = {
    "enabled": False,  # 默认禁用Docker，可根据需要启用
    "image": "python:3.11-slim",
    "network_mode": "bridge",
    "cpu_limit": 1.0,
    "memory_limit": "512m",
    "auto_remove": True,
}

# AI模型配置（不同Agent可使用不同模型）
AI_MODELS = {
    "recon_agent": {
        "api_url": None,  # None表示使用默认配置
        "api_key": None,
        "model": None,
    },
    "scanner_agent": {
        "api_url": None,
        "api_key": None,
        "model": None,
    },
    "exploit_agent": {
        "api_url": None,
        "api_key": None,
        "model": None,
    },
    "post_exploit_agent": {
        "api_url": None,
        "api_key": None,
        "model": None,
    },
    "tunnel_agent": {
        "api_url": None,
        "api_key": None,
        "model": None,
    },
}

# 协作模式配置
COLLABORATION_MODES = {
    "default": "hybrid",  # 默认混合模式
    "parallel": {
        "max_concurrent_agents": 5,  # 最大并发Agent数
    },
    "pipeline": {
        "stages": ["recon", "scan", "exploit", "post_exploit"],  # 流水线阶段
        "auto_proceed": True,  # 是否自动进入下一阶段
    },
    "orchestrated": {
        "master_agent": "orchestrator",  # 主协调Agent
        "decision_threshold": 0.7,  # 决策阈值
    },
}

# 工具执行配置
TOOL_EXECUTION = {
    "default_timeout": 300,  # 默认超时时间（秒）
    "use_cache": True,  # 是否使用结果缓存
    "cache_ttl": 3600,  # 缓存TTL（秒）
    "max_retries": 3,  # 最大重试次数
    "retry_delay": 5,  # 重试延迟（秒）
}

# 工具特定配置
TOOL_SPECIFIC_CONFIG = {
    "nmap": {
        "default_scan_type": "syn",
        "default_ports": "1-1000",
        "output_format": "xml",
    },
    "masscan": {
        "default_rate": 1000,  # 包/秒
        "default_ports": "1-1000",
    },
    "nuclei": {
        "template_path": None,
        "rate_limit": 150,
        "timeout": 10,
    },
    "xray": {
        "default_scan_type": "webscan",
        "webhook_enabled": False,
    },
    "sqlmap": {
        "batch_mode": True,
        "risk_level": 1,
        "level": 1,
    },
    "commix": {
        "default_os_cmd": "whoami",
        "batch_mode": True,
    },
    "tplmap": {
        "default_os_cmd": "whoami",
    },
    "xsstrike": {
        "default_threads": 30,
        "crawl_enabled": False,
    },
    "hydra": {
        "default_threads": 16,
    },
    "metasploit": {
        "rpc_host": "127.0.0.1",
        "rpc_port": 55553,
        "rpc_user": "msf",
        "rpc_pass": None,
    },
    "fscan": {
        "threads": 600,
        "timeout": 3,
    },
    "ligolo": {
        "default_listen_port": 11601,
    },
}

# 共享知识库配置
KNOWLEDGE_BASE_CONFIG = {
    "auto_deduplicate": True,  # 自动去重
    "deduplicate_interval": 300,  # 去重间隔（秒）
    "max_entries": 10000,  # 最大条目数
    "cleanup_old_entries": True,  # 清理旧条目
    "entry_ttl": 86400,  # 条目TTL（秒，24小时）
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "file": None,  # None表示只输出到控制台
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

def get_tool_path(tool_name: str) -> Optional[str]:
    """获取工具路径"""
    return TOOL_PATHS.get(tool_name.lower())

def is_docker_enabled() -> bool:
    """检查Docker是否启用"""
    return DOCKER_CONFIG.get("enabled", False)

def get_ai_config(agent_name: str) -> Dict[str, Any]:
    """获取Agent的AI配置"""
    return AI_MODELS.get(agent_name, {})

def get_tool_config(tool_name: str) -> Dict[str, Any]:
    """获取工具的特定配置"""
    return TOOL_SPECIFIC_CONFIG.get(tool_name.lower(), {})

def update_config(config_key: str, value: Any):
    """更新配置（运行时）"""
    # 这里可以实现配置的动态更新逻辑
    pass
