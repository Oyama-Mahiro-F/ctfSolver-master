"""
GTFOBins知识库 - 系统二进制文件提权知识库
"""
import json
import os
from typing import Dict, Any, List, Optional
from utils.logger import logger


class GTFOBinsKnowledge:
    """GTFOBins知识库 - 提供系统二进制文件提权方法查询"""
    
    def __init__(self, data_path: Optional[str] = None):
        """
        初始化GTFOBins知识库
        
        Args:
            data_path: GTFOBins数据文件路径（JSON格式）
        """
        self.data_path = data_path or os.path.join(
            os.path.dirname(__file__),
            "../../config/knowledge/gtfobins.json"
        )
        self.data: Dict[str, Any] = {}
        self._load_data()
    
    def _load_data(self):
        """加载GTFOBins数据"""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"GTFOBins知识库已加载: {len(self.data)} 个二进制文件")
            except Exception as e:
                logger.error(f"加载GTFOBins数据失败: {e}")
                self.data = {}
        else:
            logger.warning(f"GTFOBins数据文件不存在: {self.data_path}")
            self.data = {}
    
    def query(self, binary_name: str, sudo_available: bool = False) -> Dict[str, Any]:
        """
        查询二进制文件的提权方法
        
        Args:
            binary_name: 二进制文件名（如 vim, nano, python等）
            sudo_available: 是否有sudo权限
            
        Returns:
            Dict: 提权方法信息
        """
        binary_name = binary_name.lower()
        
        if binary_name not in self.data:
            return {
                "found": False,
                "binary": binary_name,
                "methods": []
            }
        
        binary_data = self.data[binary_name]
        methods = []
        
        # 提取提权方法
        if sudo_available and "sudo" in binary_data:
            methods.extend(binary_data["sudo"])
        elif "suid" in binary_data:
            methods.extend(binary_data["suid"])
        elif "capabilities" in binary_data:
            methods.extend(binary_data["capabilities"])
        
        return {
            "found": True,
            "binary": binary_name,
            "methods": methods,
            "description": binary_data.get("description", "")
        }
    
    def search(self, keyword: str) -> List[str]:
        """
        搜索包含关键字的二进制文件
        
        Args:
            keyword: 搜索关键字
            
        Returns:
            List[str]: 匹配的二进制文件名列表
        """
        keyword = keyword.lower()
        matches = []
        
        for binary_name in self.data.keys():
            if keyword in binary_name.lower():
                matches.append(binary_name)
        
        return matches
    
    def get_all_binaries(self) -> List[str]:
        """获取所有二进制文件列表"""
        return list(self.data.keys())


# 全局实例
gtfobins_knowledge = GTFOBinsKnowledge()
