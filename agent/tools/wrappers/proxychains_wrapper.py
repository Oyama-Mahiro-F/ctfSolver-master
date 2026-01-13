"""
ProxyChains包装器 - 强制工具走代理
"""
import os
import subprocess
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class ProxyChainsWrapper(ToolBase):
    """ProxyChains工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="proxychains",
            description="强制工具走代理"
        )
        self.required_params = ["command"]
        self.optional_params = ["proxy_config", "proxy_type", "proxy_host", "proxy_port"]
        self.proxychains_path = get_tool_path("proxychains") or "proxychains"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行ProxyChains命令"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            command = params["command"]  # 要执行的命令
            proxy_config = params.get("proxy_config")
            proxy_type = params.get("proxy_type", "socks5")
            proxy_host = params.get("proxy_host", "127.0.0.1")
            proxy_port = params.get("proxy_port", 1080)
            
            # 构建ProxyChains命令
            cmd = [self.proxychains_path]
            
            # 如果提供了代理配置，使用配置文件
            if proxy_config:
                cmd.extend(["-f", proxy_config])
            else:
                # 使用环境变量或默认配置
                # 可以通过环境变量设置代理
                env = os.environ.copy()
                env["PROXYCHAINS_CONF_FILE"] = self._create_temp_config(proxy_type, proxy_host, proxy_port)
            
            # 添加要执行的命令
            if isinstance(command, list):
                cmd.extend(command)
            else:
                cmd.extend(command.split())
            
            # 执行命令
            logger.info(f"执行ProxyChains: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env=env if 'env' in locals() else None
            )
            
            if result.returncode == 0:
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    data={
                        "output": result.stdout,
                        "command": command
                    },
                    raw_output=result.stdout
                )
            else:
                return ToolResult(
                    status=ToolResultStatus.FAILURE,
                    error=result.stderr,
                    data={"output": result.stdout}
                )
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolResultStatus.TIMEOUT,
                error="ProxyChains执行超时"
            )
        except Exception as e:
            logger.error(f"ProxyChains执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _create_temp_config(self, proxy_type: str, proxy_host: str, proxy_port: int) -> str:
        """创建临时ProxyChains配置文件"""
        import tempfile
        config_content = f"""
[ProxyList]
{proxy_type} {proxy_host} {proxy_port}
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False)
        temp_file.write(config_content)
        temp_file.close()
        return temp_file.name
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return {"output": raw_output}
