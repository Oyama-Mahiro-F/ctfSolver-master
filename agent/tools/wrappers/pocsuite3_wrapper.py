"""
Pocsuite3包装器 - Python PoC/EXP框架
"""
import os
import subprocess
import json
from typing import Dict, Any
from ..base import ToolBase, ToolResult, ToolResultStatus
from utils.logger import logger
from config.penetration_config import get_tool_path


class Pocsuite3Wrapper(ToolBase):
    """Pocsuite3工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="pocsuite3",
            description="Python PoC/EXP框架，对国内组件支持较好"
        )
        self.required_params = ["target"]
        self.optional_params = ["poc_file", "poc_name", "mode", "verify"]
        self.pocsuite3_path = get_tool_path("pocsuite3") or "pocsuite3"
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行Pocsuite3 PoC"""
        try:
            is_valid, error_msg = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error=error_msg
                )
            
            target = params["target"]  # URL或IP
            poc_file = params.get("poc_file")
            poc_name = params.get("poc_name")
            mode = params.get("mode", "verify")  # verify或attack
            verify = params.get("verify", True)
            
            # 构建Pocsuite3命令
            cmd = [self.pocsuite3_path]
            
            # 目标
            cmd.extend(["-u", target])
            
            # PoC文件或名称
            if poc_file:
                cmd.extend(["-r", poc_file])
            elif poc_name:
                cmd.extend(["-k", poc_name])
            else:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    error="需要指定poc_file或poc_name"
                )
            
            # 模式
            if mode == "attack":
                cmd.append("--attack")
            elif verify:
                cmd.append("--verify")
            
            # JSON输出
            cmd.append("--json")
            
            # 执行命令
            logger.info(f"执行Pocsuite3: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # 解析输出
            parsed_data = self._parse_output(result.stdout)
            
            if result.returncode == 0 or parsed_data.get("vulnerable"):
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
                error="Pocsuite3执行超时"
            )
        except Exception as e:
            logger.error(f"Pocsuite3执行异常: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析Pocsuite3输出"""
        result = {
            "vulnerable": False,
            "poc_name": None,
            "target": None,
            "result": None
        }
        
        try:
            data = json.loads(output)
            result["vulnerable"] = data.get("success", False)
            result["poc_name"] = data.get("poc_name")
            result["target"] = data.get("target")
            result["result"] = data.get("result")
        except json.JSONDecodeError:
            # 文本输出解析
            if "success" in output.lower() or "vulnerable" in output.lower():
                result["vulnerable"] = True
            result["result"] = output
        
        return result
    
    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        """解析文本输出"""
        return self._parse_output(raw_output)
