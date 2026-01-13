"""
BloodHound包装器 - 域分析
"""
import os
import subprocess
import json
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class BloodHoundWrapper(ToolBase):
    """BloodHound工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="bloodhound",
            description="域分析工具，使用SharpHound采集数据"
        )
        self.required_params = ["target_domain"]
        self.optional_params = ["collection_method", "credentials", "output_dir"]
        self.bloodhound_path = get_tool_path("bloodhound") or "bloodhound"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行BloodHound数据采集"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target_domain = params["target_domain"]
            collection_method = params.get("collection_method", "SharpHound")
            credentials = params.get("credentials")
            output_dir = params.get("output_dir", "/tmp/bloodhound")
            
            # BloodHound需要先使用SharpHound采集数据
            # 然后在BloodHound中导入分析
            if collection_method == "SharpHound":
                # 返回SharpHound执行指令
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    data={
                        "instruction": "需要在域内机器上执行SharpHound采集数据",
                        "command": f"SharpHound.exe -c All -d {target_domain}",
                        "output_dir": output_dir,
                        "note": "采集完成后，将JSON文件导入BloodHound进行分析"
                    }
                )
            else:
                # 直接使用BloodHound CLI（如果支持）
                cmd = [self.bloodhound_path, "-d", target_domain]
                if output_dir:
                    cmd.extend(["-o", output_dir])
                
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
            logger.error(f"BloodHound执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析BloodHound输出"""
        # BloodHound主要输出JSON数据文件
        # 这里返回解析后的图谱数据摘要
        result = {
            "nodes": [],
            "edges": [],
            "summary": {
                "total_nodes": 0,
                "total_edges": 0,
                "critical_paths": []
            }
        }
        
        # 如果输出是JSON，尝试解析
        try:
            data = json.loads(output)
            if "nodes" in data:
                result["nodes"] = data["nodes"]
            if "edges" in data:
                result["edges"] = data["edges"]
            
            result["summary"]["total_nodes"] = len(result["nodes"])
            result["summary"]["total_edges"] = len(result["edges"])
        except json.JSONDecodeError:
            result["raw_output"] = output
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
