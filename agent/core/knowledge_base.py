"""
共享知识库 - Agent间信息共享机制
"""
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from utils.logger import logger


class ResultType(Enum):
    """结果类型枚举"""
    RECON = "recon"  # 侦察结果
    VULN = "vuln"  # 漏洞
    EXPLOIT = "exploit"  # 利用结果
    POST_EXPLOIT = "post_exploit"  # 后渗透结果
    TUNNEL = "tunnel"  # 隧道信息
    GENERAL = "general"  # 通用信息


@dataclass
class KnowledgeEntry:
    """知识库条目"""
    id: str
    type: ResultType
    source: str  # 来源Agent
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    related_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "related_ids": self.related_ids
        }


class SharedContext:
    """共享上下文 - 存储所有Agent的发现结果"""
    
    def __init__(self):
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.index_by_type: Dict[ResultType, List[str]] = {rt: [] for rt in ResultType}
        self.index_by_source: Dict[str, List[str]] = {}
        self.index_by_tag: Dict[str, List[str]] = {}
    
    def add(self, 
            entry_type: ResultType,
            source: str,
            data: Dict[str, Any],
            entry_id: Optional[str] = None,
            tags: Optional[List[str]] = None,
            related_ids: Optional[List[str]] = None) -> str:
        """
        添加知识条目
        
        Args:
            entry_type: 结果类型
            source: 来源Agent
            data: 数据
            entry_id: 条目ID（自动生成如果为None）
            tags: 标签列表
            related_ids: 相关条目ID列表
            
        Returns:
            str: 条目ID
        """
        if entry_id is None:
            # 原实现用毫秒时间戳，同一毫秒内的同类型条目会生成相同 id，
            # 导致后写入的条目覆盖前一条并破坏索引
            entry_id = f"{entry_type.value}_{uuid.uuid4().hex}"
        
        entry = KnowledgeEntry(
            id=entry_id,
            type=entry_type,
            source=source,
            data=data,
            tags=tags or [],
            related_ids=related_ids or []
        )
        
        self.entries[entry_id] = entry
        
        # 更新索引
        self.index_by_type[entry_type].append(entry_id)
        if source not in self.index_by_source:
            self.index_by_source[source] = []
        self.index_by_source[source].append(entry_id)
        
        for tag in entry.tags:
            if tag not in self.index_by_tag:
                self.index_by_tag[tag] = []
            self.index_by_tag[tag].append(entry_id)
        
        logger.info(f"添加知识条目: {entry_id} (类型: {entry_type.value}, 来源: {source})")
        return entry_id
    
    def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """获取条目"""
        return self.entries.get(entry_id)
    
    def query(self,
              entry_type: Optional[ResultType] = None,
              source: Optional[str] = None,
              tag: Optional[str] = None,
              since: Optional[float] = None,
              limit: Optional[int] = None) -> List[KnowledgeEntry]:
        """
        查询条目
        
        Args:
            entry_type: 结果类型过滤
            source: 来源过滤
            tag: 标签过滤
            since: 时间戳过滤（只返回此时间之后的条目）
            limit: 结果数量限制
            
        Returns:
            List[KnowledgeEntry]: 匹配的条目列表
        """
        candidate_ids = set(self.entries.keys())
        
        # 按类型过滤
        if entry_type:
            candidate_ids &= set(self.index_by_type[entry_type])
        
        # 按来源过滤
        if source:
            if source in self.index_by_source:
                candidate_ids &= set(self.index_by_source[source])
            else:
                return []
        
        # 按标签过滤
        if tag:
            if tag in self.index_by_tag:
                candidate_ids &= set(self.index_by_tag[tag])
            else:
                return []
        
        # 按时间过滤
        if since:
            candidate_ids = {
                eid for eid in candidate_ids
                if self.entries[eid].timestamp >= since
            }
        
        # 获取条目并排序（按时间倒序）
        results = [self.entries[eid] for eid in candidate_ids]
        results.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 限制数量
        if limit:
            results = results[:limit]
        
        return results
    
    def get_related(self, entry_id: str) -> List[KnowledgeEntry]:
        """获取相关条目"""
        entry = self.get(entry_id)
        if not entry:
            return []
        
        related = []
        for related_id in entry.related_ids:
            related_entry = self.get(related_id)
            if related_entry:
                related.append(related_entry)
        
        return related
    
    def link(self, entry_id1: str, entry_id2: str):
        """关联两个条目"""
        entry1 = self.get(entry_id1)
        entry2 = self.get(entry_id2)
        
        if entry1 and entry2:
            if entry_id2 not in entry1.related_ids:
                entry1.related_ids.append(entry_id2)
            if entry_id1 not in entry2.related_ids:
                entry2.related_ids.append(entry_id1)
            logger.info(f"关联条目: {entry_id1} <-> {entry_id2}")
    
    def remove(self, entry_id: str) -> bool:
        """删除条目"""
        entry = self.get(entry_id)
        if not entry:
            return False
        
        # 从索引中移除
        self.index_by_type[entry.type].remove(entry_id)
        if entry.source in self.index_by_source:
            self.index_by_source[entry.source].remove(entry_id)
        for tag in entry.tags:
            if tag in self.index_by_tag:
                self.index_by_tag[tag].remove(entry_id)
        
        # 从其他条目的related_ids中移除
        for other_entry in self.entries.values():
            if entry_id in other_entry.related_ids:
                other_entry.related_ids.remove(entry_id)
        
        del self.entries[entry_id]
        logger.info(f"删除知识条目: {entry_id}")
        return True
    
    def deduplicate(self, similarity_threshold: float = 0.9) -> int:
        """
        自动去重
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            int: 删除的重复条目数量
        """
        # 简单的去重逻辑：基于数据内容的哈希
        seen_hashes = {}
        to_remove = []
        
        for entry_id, entry in self.entries.items():
            # 生成数据哈希
            data_str = json.dumps(entry.data, sort_keys=True)
            data_hash = hash(data_str)
            
            if data_hash in seen_hashes:
                # 发现重复，保留时间更早的
                existing_id = seen_hashes[data_hash]
                existing_entry = self.entries[existing_id]
                
                if entry.timestamp < existing_entry.timestamp:
                    # 当前条目更早，删除已存在的
                    to_remove.append(existing_id)
                    seen_hashes[data_hash] = entry_id
                else:
                    # 已存在的更早，删除当前条目
                    to_remove.append(entry_id)
            else:
                seen_hashes[data_hash] = entry_id
        
        # 删除重复条目
        for entry_id in to_remove:
            self.remove(entry_id)
        
        return len(to_remove)
    
    def export(self) -> Dict[str, Any]:
        """导出所有数据"""
        return {
            "entries": {eid: entry.to_dict() for eid, entry in self.entries.items()},
            "stats": {
                "total_entries": len(self.entries),
                "by_type": {rt.value: len(self.index_by_type[rt]) for rt in ResultType},
                "by_source": {src: len(ids) for src, ids in self.index_by_source.items()}
            }
        }
    
    def clear(self):
        """清空所有数据"""
        self.entries.clear()
        self.index_by_type = {rt: [] for rt in ResultType}
        self.index_by_source.clear()
        self.index_by_tag.clear()
        logger.info("共享上下文已清空")


class ResultAggregator:
    """结果聚合器 - 合并多个Agent的结果并生成报告"""
    
    def __init__(self, shared_context: SharedContext):
        self.context = shared_context
    
    def aggregate_recon_results(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """聚合侦察结果"""
        recon_entries = self.context.query(entry_type=ResultType.RECON, limit=limit)
        
        aggregated = {
            "total_findings": len(recon_entries),
            "hosts": [],
            "ports": [],
            "services": [],
            "domains": [],
            "technologies": []
        }
        
        for entry in recon_entries:
            data = entry.data
            if "hosts" in data:
                aggregated["hosts"].extend(data["hosts"])
            if "ports" in data:
                aggregated["ports"].extend(data["ports"])
            if "services" in data:
                aggregated["services"].extend(data["services"])
            if "domains" in data:
                aggregated["domains"].extend(data["domains"])
            if "technologies" in data:
                aggregated["technologies"].extend(data["technologies"])
        
        # 去重
        aggregated["hosts"] = list(set(aggregated["hosts"]))
        aggregated["ports"] = list(set(aggregated["ports"]))
        aggregated["domains"] = list(set(aggregated["domains"]))
        
        return aggregated
    
    def aggregate_vuln_results(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """聚合漏洞结果"""
        vuln_entries = self.context.query(entry_type=ResultType.VULN, limit=limit)
        
        aggregated = {
            "total_vulns": len(vuln_entries),
            "vulns_by_type": {},
            "vulns_by_severity": {"critical": [], "high": [], "medium": [], "low": []},
            "vulns": []
        }
        
        for entry in vuln_entries:
            data = entry.data
            vuln_type = data.get("type", "unknown")
            severity = data.get("severity", "medium")
            
            if vuln_type not in aggregated["vulns_by_type"]:
                aggregated["vulns_by_type"][vuln_type] = []
            aggregated["vulns_by_type"][vuln_type].append(entry.id)
            
            if severity in aggregated["vulns_by_severity"]:
                aggregated["vulns_by_severity"][severity].append(entry.id)
            
            aggregated["vulns"].append({
                "id": entry.id,
                "type": vuln_type,
                "severity": severity,
                "target": data.get("target", ""),
                "description": data.get("description", "")
            })
        
        return aggregated
    
    def generate_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        report = {
            "timestamp": time.time(),
            "recon": self.aggregate_recon_results(),
            "vulns": self.aggregate_vuln_results(),
            "summary": {
                "total_entries": len(self.context.entries),
                "sources": list(self.context.index_by_source.keys()),
                "entry_types": {rt.value: len(self.context.index_by_type[rt]) for rt in ResultType}
            }
        }
        
        return report
    
    def identify_key_paths(self) -> List[Dict[str, Any]]:
        """识别关键攻击路径"""
        # 简单的路径识别：基于漏洞和利用结果的关联
        key_paths = []
        
        vuln_entries = self.context.query(entry_type=ResultType.VULN)
        exploit_entries = self.context.query(entry_type=ResultType.EXPLOIT)
        
        # 建立漏洞到利用的映射
        for exploit_entry in exploit_entries:
            related_vulns = [
                self.context.get(rid) 
                for rid in exploit_entry.related_ids
                if self.context.get(rid) and self.context.get(rid).type == ResultType.VULN
            ]
            
            if related_vulns:
                path = {
                    "vulns": [v.to_dict() for v in related_vulns],
                    "exploit": exploit_entry.to_dict(),
                    "success": exploit_entry.data.get("success", False)
                }
                key_paths.append(path)
        
        return key_paths


# 全局共享上下文实例
shared_context = SharedContext()
