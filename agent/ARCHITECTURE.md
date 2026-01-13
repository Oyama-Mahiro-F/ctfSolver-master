# 多AI协作渗透测试系统架构说明

## 架构概述

本系统采用**"主AI调度+多AI并行"**的架构模式：

```
用户任务
  ↓
MasterOrchestrator（主AI协调器）
  ├─ 使用LLM分析任务上下文
  ├─ 查询共享知识库
  ├─ 智能决策：任务分解和分配
  └─ 协调多个专业AI并行工作
       ├─ ReconAgent（并行执行）
       ├─ ScannerAgent（并行执行）
       ├─ ExploitAgent（并行执行）
       ├─ PostExploitAgent（并行执行）
       └─ TunnelAgent（按需执行）
            ↓
      共享知识库（SharedContext）
            ↓
      结果聚合和报告生成
```

## 核心组件

### 1. 主AI协调器（MasterOrchestrator）

**位置**: `agent/core/master_orchestrator.py`

**功能**:
- 使用LLM进行智能任务调度和决策
- 分析任务上下文、依赖关系、系统状态
- 查询共享知识库获取相关信息
- 动态分配任务给合适的Agent
- 协调多个Agent并行工作

**特点**:
- 基于LLM的智能决策，而非简单规则
- 支持任务分解（将复杂任务分解为子任务）
- 支持并行任务识别和执行
- 回退机制：LLM决策失败时使用规则回退

### 2. 专业AI Agent

**位置**: `agent/agents/penetration/`

每个Agent都是独立的专业AI，负责特定领域的任务：

- **ReconAgent**: 信息收集和资产发现
  - 工具：Nmap, Masscan, Subfinder, WhatWeb, FFuf
  
- **ScannerAgent**: 漏洞扫描和发现
  - 工具：Nuclei, Xray, SearchSploit
  
- **ExploitAgent**: 漏洞利用和权限获取
  - 工具：SQLMap, Commix, Tplmap, XSStrike, Hydra, Pocsuite3, Metasploit
  
- **PostExploitAgent**: 后渗透和横向移动
  - 工具：PEAS, Mimikatz, LaZagne, Fscan, Impacket, NetExec, BloodHound, GTFOBins
  
- **TunnelAgent**: 代理和隧道建立
  - 工具：Chisel, Frp, Ligolo-ng, ProxyChains

### 3. 工具中间件层

**位置**: `agent/tools/`

**组件**:
- **ToolBase**: 工具基类，定义统一接口
- **ToolRegistry**: 工具注册系统，动态发现和管理工具
- **ToolExecutor**: 工具执行器，支持Docker和本地执行
- **DockerManager**: Docker沙箱管理
- **工具包装器**: 统一工具输入输出格式

**特点**:
- 所有工具输出标准化为JSON格式
- 支持Docker沙箱执行（安全）
- 结果缓存机制
- 超时控制和资源限制

### 4. 共享知识库（SharedContext）

**位置**: `agent/core/knowledge_base.py`

**功能**:
- 存储所有Agent的发现结果
- 提供查询接口（按类型、时间、来源、标签）
- 自动去重和关联分析
- 结果聚合和报告生成

**数据流**:
```
Agent执行任务
  ↓
结果保存到SharedContext
  ↓
其他Agent可以查询相关发现
  ↓
避免重复工作，提高效率
```

## 工作流程

### 1. 任务提交

用户或系统提交任务到主AI协调器：

```python
task_id = master_orchestrator.add_task(
    name="端口扫描-192.168.1.1",
    task_type="recon",
    params={"target": "192.168.1.1", "scan_type": "port_scan"}
)
```

### 2. 主AI决策

主AI协调器使用LLM分析任务：

1. 分析任务类型、参数、依赖关系
2. 查询共享知识库获取相关信息
3. 查看可用Agent及其负载
4. 生成任务分配决策（JSON格式）

### 3. 任务分配

根据主AI的决策，将任务分配给合适的Agent：

```python
decision = {
    "agent_id": "recon_1",
    "reasoning": "该Agent擅长端口扫描，当前负载较低",
    "strategy": "直接执行",
    "parallel_tasks": ["task_2", "task_3"]  # 可以并行执行的任务
}
```

### 4. 并行执行

多个Agent同时执行任务：

- ReconAgent-1: 扫描 192.168.1.1
- ReconAgent-2: 枚举 example.com 子域名
- ScannerAgent-1: 扫描 http://example.com

### 5. 结果共享

所有Agent的结果保存到共享知识库：

```python
shared_context.add(
    entry_type=ResultType.RECON,
    source="recon_1",
    data=scan_result,
    tags=["port_scan", "192.168.1.1"]
)
```

### 6. 智能协作

后续任务可以查询共享知识库：

```python
# ScannerAgent查询之前的侦察结果
recon_results = shared_context.query(
    entry_type=ResultType.RECON,
    tag="192.168.1.1"
)
# 基于侦察结果进行针对性扫描
```

## 工具集成

### 已集成的工具（按阶段）

**第一阶段：信息收集**
- Nmap, Masscan, Subfinder, WhatWeb, FFuf

**第二阶段：漏洞扫描**
- Nuclei, Xray, SearchSploit

**第三阶段：Web攻击**
- SQLMap, Commix, Tplmap, XSStrike, Hydra

**第四阶段：漏洞利用**
- Metasploit, Pocsuite3

**第五阶段：后渗透**
- PEAS, Mimikatz, LaZagne, GTFOBins（知识库）

**第六阶段：横向移动**
- Fscan, Impacket, NetExec, BloodHound

**第七阶段：隧道**
- Chisel, Frp, Ligolo-ng, ProxyChains

### 工具输出标准化

所有工具的输出都统一为JSON格式：

```json
{
    "status": "success",
    "data": {
        "hosts": [...],
        "ports": [...],
        "summary": {...}
    },
    "execution_time": 12.5
}
```

## 配置说明

### 主AI模型配置

在 `config/penetration_config.py` 中配置：

```python
AI_MODELS = {
    "master_orchestrator": {
        "api_url": None,  # 使用config.py中的默认配置
        "api_key": None,
        "model": None,
    }
}
```

### 工具路径配置

```python
TOOL_PATHS = {
    "nmap": "nmap",
    "nuclei": "nuclei",
    # ... 所有工具路径
}
```

## 使用示例

### 基本使用

```python
from core.master_orchestrator import MasterOrchestrator
from agents.penetration import ReconAgent, ScannerAgent

# 创建主AI协调器
master = MasterOrchestrator()

# 注册Agent
master.register_agent("recon_1", "ReconAgent", ["recon"])
master.register_agent("scanner_1", "ScannerAgent", ["scan"])

# 注册任务处理器
async def recon_handler(params, agent_id):
    agent = ReconAgent(agent_id, master.shared_context)
    return await agent.execute_recon(params)

master.register_task_handler("recon", recon_handler)

# 添加任务
task_id = master.add_task(
    name="端口扫描",
    task_type="recon",
    params={"target": "192.168.1.1", "scan_type": "port_scan"}
)

# 启动协调器
master.start()
await master.run()
```

## 架构优势

1. **智能调度**: 主AI根据上下文智能分配任务，而非简单规则
2. **并行执行**: 多个Agent同时工作，提高效率
3. **知识共享**: 所有Agent共享发现，避免重复工作
4. **动态调整**: 根据执行结果动态调整策略
5. **工具统一**: 所有工具统一接口，输出标准化
6. **可扩展**: 易于添加新工具和新Agent

## 与原有系统集成

- 复用现有的 `agent_manager.py` 进行Agent注册和心跳
- 复用现有的消息系统进行Agent间通信
- 扩展现有的Flask API支持新工具调用
- 保持与现有CTF解题功能的兼容性
