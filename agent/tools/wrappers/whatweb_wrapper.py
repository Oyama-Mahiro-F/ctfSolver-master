"""
WhatWeb包装器 - Web指纹识别
"""
import os
import subprocess
import json
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class WhatWebWrapper(ToolBase):
    """WhatWeb工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="whatweb",
            description="Web指纹识别工具，识别CMS、框架、服务器等"
        )
        self.required_params = ["target"]
        self.optional_params = ["aggression", "verbosity"]
        self.whatweb_path = get_tool_path("whatweb") or "whatweb"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行WhatWeb扫描"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # URL
            aggression = params.get("aggression", 1)  # 1-4
            verbosity = params.get("verbosity", 0)  # 0-3
            
            # 构建WhatWeb命令
            cmd = [self.whatweb_path]
            
            # 目标URL
            cmd.append(target)
            
            # 攻击级别
            cmd.extend(["-a", str(aggression)])
            
            # 详细程度
            if verbosity > 0:
                cmd.extend(["-v", str(verbosity)])
            
            # JSON输出
            cmd.append("--log-json=-")
            
            # 执行命令
            logger.info(f"执行WhatWeb: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout)
            
            if result.returncode == 0 or parsed_data.get("technologies"):
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
                error="WhatWeb执行超时"
            )
        except Exception as e:
            logger.error(f"WhatWeb执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析WhatWeb JSON输出"""
        result = {
            "target": None,
            "technologies": [],
            "summary": {
                "cms": None,
                "framework": None,
                "server": None,
                "total_plugins": 0
            }
        }
        
        try:
            # WhatWeb输出JSON格式
            data = json.loads(output)
            
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            result["target"] = data.get("target", "")
            
            # 解析插件信息
            plugins = data.get("plugins", {})
            for plugin_name, plugin_data in plugins.items():
                tech_info = {
                    "name": plugin_name,
                    "category": plugin_data.get("category", "unknown"),
                    "version": plugin_data.get("version", []),
                    "string": plugin_data.get("string", []),
                    "account": plugin_data.get("account", []),
                    "os": plugin_data.get("os", []),
                    "script": plugin_data.get("script", [])
                }
                result["technologies"].append(tech_info)
                
                # 提取关键信息
                if plugin_name.lower() in ["wordpress", "joomla", "drupal", "magento"]:
                    result["summary"]["cms"] = plugin_name
                elif plugin_name.lower() in ["apache", "nginx", "iis"]:
                    result["summary"]["server"] = plugin_name
                elif plugin_name.lower() in ["php", "ruby", "python", "java"]:
                    result["summary"]["framework"] = plugin_name
            
            result["summary"]["total_plugins"] = len(result["technologies"])
        
        except json.JSONDecodeError:
            # 如果不是JSON，尝试解析文本输出
            result["technologies"] = [{"raw": output}]
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
