# 多AI协作渗透测试框架

## 概述

这是一个基于现有ctfSolver项目的多AI协作渗透测试框架，支持多个AI Agent协同工作，集成核心六大渗透测试工具（Nmap, Nuclei, SQLMap, Metasploit, Fscan, Impacket），提供统一的工具接口和多种协作模式。

## 架构设计

### 核心组件

1. **工具中间件层** (`agent/tools/`)
   - `base.py`: 工具基类，定义统一接口
   - `registry.py`: 工具注册系统
   - `executor.py`: 工具执行器（支持Docker和本地执行）
   - `docker_manager.py`: Docker沙箱管理
   - `wrappers/`: 工具包装器（统一输入输出格式）

2. **多AI协作引擎** (`agent/core/`)
   - `orchestrator.py`: 主协调器，支持多种协作模式
   - `knowledge_base.py`: 共享知识库，Agent间信息共享
   - `task_queue.py`: 任务队列管理

3. **渗透测试Agent** (`agent/agents/penetration/`)
   - `recon_agent.py`: 侦察Agent
   - `scanner_agent.py`: 扫描Agent
   - `exploit_agent.py`: 利用Agent
   - `post_exploit_agent.py`: 后渗透Agent
   - `tunnel_agent.py`: 隧道Agent

4. **配置管理** (`agent/config/`)
   - `penetration_config.py`: 渗透测试工具配置

## 协作模式

### 1. 并行模式 (Parallel)
多个Agent同时执行独立任务，适合大规模并行扫描。

### 2. 流水线模式 (Pipeline)
按阶段顺序执行：侦察 → 扫描 → 利用 → 后渗透，每个阶段完成后自动进入下一阶段。

### 3. 编排模式 (Orchestrated)
主AI根据任务动态分配子任务给专业AI，智能决策任务分配。

### 4. 混合模式 (Hybrid)
结合以上多种方式，根据任务类型自动选择最优执行策略。

## 集成工具

### 核心六大工具

1. **Nmap** - 端口扫描和服务识别
2. **Nuclei** - 基于模板的漏洞扫描
3. **SQLMap** - SQL注入检测和利用
4. **Metasploit** - 漏洞利用框架（通过RPC）
5. **Fscan** - 内网综合扫描
6. **Impacket** - Windows协议利用工具集

### 工具包装器

所有工具都通过包装器统一接口，输出格式标准化为JSON，便于AI理解。

## 使用方法

### 基本使用

```python
from core.orchestrator import Orchestrator, CollaborationMode
from core.knowledge_base import SharedContext
from agents.penetration import ReconAgent, ScannerAgent
from tools.registry import tool_registry
from tools.wrappers import NmapWrapper, NucleiWrapper

# 创建协调器
orchestrator = Orchestrator(mode=CollaborationMode.HYBRID)

# 注册Agent
orchestrator.register_agent("recon_1", "ReconAgent", ["recon"], max_concurrent_tasks=2)
orchestrator.register_agent("scanner_1", "ScannerAgent", ["scan"], max_concurrent_tasks=2)

# 注册工具
tool_registry.register(NmapWrapper())
tool_registry.register(NucleiWrapper())

# 注册任务处理器
async def recon_handler(params, agent_id):
    agent = ReconAgent(agent_id, orchestrator.shared_context)
    return await agent.execute_recon(params)

orchestrator.register_task_handler("recon", recon_handler)

# 添加任务
task_id = orchestrator.add_task(
    name="端口扫描",
    task_type="recon",
    params={"target": "192.168.1.1", "scan_type": "port_scan"}
)

# 启动协调器
orchestrator.start()
await orchestrator.run()
```

### 工具调用示例

```python
from tools.executor import tool_executor

# 执行Nmap扫描
result = tool_executor.execute("nmap", {
    "target": "192.168.1.1",
    "ports": "1-1000",
    "scan_type": "syn",
    "service_version": True
})

if result.status.value == "success":
    print(result.data)
```

### Agent使用示例

```python
from agents.penetration import ReconAgent
from core.knowledge_base import SharedContext

shared_context = SharedContext()
agent = ReconAgent("recon_1", shared_context)

# 执行侦察任务
result = await agent.execute_recon({
    "target": "192.168.1.1",
    "scan_type": "port_scan",
    "port_scan_options": {
        "ports": "1-1000",
        "scan_type": "syn"
    }
})
```

## 配置说明

### 工具路径配置

编辑 `agent/config/penetration_config.py`:

```python
TOOL_PATHS = {
    "nmap": "nmap",  # 系统PATH中的命令
    "nuclei": "nuclei",
    "sqlmap": "sqlmap",
    # ...
}
```

### Docker配置

```python
DOCKER_CONFIG = {
    "enabled": False,  # 是否启用Docker
    "image": "python:3.11-slim",
    "network_mode": "bridge",
    "cpu_limit": 1.0,
    "memory_limit": "512m",
}
```

### AI模型配置

可以为不同Agent配置不同的AI模型：

```python
AI_MODELS = {
    "recon_agent": {
        "api_url": None,
        "api_key": None,
        "model": None,
    },
    # ...
}
```

## 文件结构

```
agent/
├── core/
│   ├── orchestrator.py          # 多AI协作引擎
│   ├── knowledge_base.py        # 共享知识库
│   └── task_queue.py            # 任务队列
├── agents/
│   └── penetration/             # 渗透测试专用Agent
│       ├── recon_agent.py
│       ├── scanner_agent.py
│       ├── exploit_agent.py
│       ├── post_exploit_agent.py
│       └── tunnel_agent.py
├── tools/
│   ├── base.py                  # 工具基类
│   ├── executor.py              # 工具执行器
│   ├── registry.py              # 工具注册系统
│   ├── docker_manager.py        # Docker管理
│   └── wrappers/                # 工具包装器
│       ├── nmap_wrapper.py
│       ├── nuclei_wrapper.py
│       ├── sqlmap_wrapper.py
│       ├── metasploit_wrapper.py
│       ├── fscan_wrapper.py
│       └── impacket_wrapper.py
├── config/
│   └── penetration_config.py    # 渗透测试配置
└── examples/
    └── multi_ai_example.py      # 使用示例
```

## 特性

1. **统一工具接口**: 所有工具通过统一接口调用，输出格式标准化
2. **Docker沙箱**: 危险工具可在Docker容器中执行，确保安全
3. **异步执行**: 支持工具并发执行，提高效率
4. **结果缓存**: 相同参数的工具调用使用缓存结果
5. **共享知识库**: Agent间信息共享，避免重复工作
6. **任务队列**: 支持任务优先级和依赖管理
7. **多种协作模式**: 支持并行、流水线、编排、混合等多种模式

## 依赖安装

```bash
# 基础依赖
pip install docker msgpack

# 工具依赖（需要单独安装）
# - Nmap: sudo apt-get install nmap
# - Nuclei: 从GitHub下载二进制文件
# - SQLMap: pip install sqlmap
# - Metasploit: 需要安装Metasploit Framework
# - Fscan: 从GitHub下载二进制文件
# - Impacket: pip install impacket
```

## 注意事项

1. **工具安装**: 确保所有工具都已正确安装并在系统PATH中
2. **权限要求**: 某些工具（如Nmap的SYN扫描）需要root权限
3. **Docker**: 如果使用Docker执行，需要安装Docker并确保服务运行
4. **Metasploit RPC**: 使用Metasploit需要先启动RPC服务：`msfrpcd -P <password> -a 127.0.0.1 -p 55553`
5. **安全**: 所有工具都应在授权环境中使用，遵守法律法规

## 扩展开发

### 添加新工具

1. 创建工具包装器类，继承`ToolBase`
2. 实现`execute()`和`parse_output()`方法
3. 在`tool_registry`中注册工具

### 添加新Agent

1. 创建Agent类
2. 实现任务处理方法
3. 在`orchestrator`中注册Agent和任务处理器

## 示例

查看 `agent/examples/multi_ai_example.py` 了解详细使用示例。

## 许可证

与主项目保持一致。

## 贡献

欢迎提交Issue和Pull Request。
