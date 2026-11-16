# ctfSolver · 二次开发版

大语言模型驱动的 CTF 自动解题框架。本仓库在原版基础上**修复了运行链路**、**重写了工具执行层**，并**补齐了自动化测试套件**。

> **原项目**：腾讯云 AI 渗透智能体黑客松参赛作品，由西安交通大学 **xjtuHunter** 队伍开发，获第二名；原维护者九暑（passerW）。
>
> **本仓库**：在原版代码上做的修复与增强，全部改动范围见下文「与原版的差异」。原项目作者不对本仓库的改动负责，原版的荣誉与设计归属原作者。

---

## 项目概况

ctfSolver 面向 CTF 竞赛与 Web 渗透场景，由五个智能体协同完成「页面探索 → 漏洞扫描 → 解法生成 → 动作执行 → Flag 提取」的闭环。

| 智能体 | 职责 |
|---|---|
| `explorer` | 爬取目标页面结构、JS 与 API 端点 |
| `scanner` | XSS / SQL 注入 / 命令注入 / LFI / IDOR 等漏洞探测 |
| `solutioner` | 依据扫描结果生成利用思路 |
| `actioner` | 决定调用哪个工具、按什么顺序执行 |
| `executor` | 实际执行 HTTP 请求、Python 与 Shell 命令 |

工具层内置 HTTP 请求、Python 执行、Shell 执行、Base64 / JSFuck 解码、PHP Filter Chain 生成等能力，可通过 `agent/config/addons.txt` 注册扩展。仓库同时包含 Flask 后端与前端界面，用于任务下发与进度监控。

---

## 与原版的差异

原版在本地运行时会卡在启动链路，任务下发后无法走完一次完整执行。本仓库的改动集中在三处：让链路能跑通、让工具调用可控、让改动可验证。

| 层次 | 主要文件 | 改动行数 | 处理的问题 |
|---|---|---|---|
| 工具层 | `agent/addons/request.py` | 226 | 统一 HTTP 请求封装、异常与超时处理 |
| 工具层 | `agent/addons/run_shell.py` | 88 | 命令执行、超时控制、退出码解析 |
| 工具层 | `agent/addons/run_python.py` | 57 | 脚本执行与输出长度截断 |
| 智能体 | `agent/agents/actioner.py` | 138 | 工具调用决策、失败重试与动作收敛 |
| 智能体 | `agent/agents/poc.py` | 93 | PoC 生成与验证循环 |
| 智能体 | `agent/agents/vulner.py`、`vulns/*` | 45 起 | 漏洞类型识别与分发，适配新的工具接口 |
| 编排 | `agent/core/orchestrator.py` | 59 | 多智能体任务流转与状态同步 |
| 编排 | `agent/core/task_queue.py` | 9 | 任务队列调度 |
| 配置 | `agent/config/config.py` | 37 | 模型与运行参数统一配置 |
| 入口 | `agent/flaghunter.py` | 72 | 启动流程与异常退出处理 |

### 两个花时间最多的问题

**一、工具单次返回内容过长，模型注意力被无关信息占据。**
原版把工具原始输出整段塞回对话，一次页面爬取就能吃掉大半个上下文。改动是在工具层做输出截断与结构化摘要，只把与当前子目标相关的部分交给模型，长输出落到文件里按需再读。

**二、工具调用失败后状态无法回退，链路带着脏状态继续跑。**
一次请求超时或命令非零退出，后续步骤仍然基于上一次的中间结果推进，错误会一直滚到最后一层。改动是给每步动作保留可回滚的快照，失败时退到上一个一致状态再重试，并设定重试上限避免死循环。

---

## 快速开始

详细步骤见 [`运行指南.md`](运行指南.md)，环境说明见 [`环境说明.md`](环境说明.md)。

### 环境

- Python 3.8+
- SQLite3
- 需要大模型 API Key 才能实际解题（DeepSeek 或腾讯云）

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r agent\requirements.txt
.\venv\Scripts\python.exe -m pip install -r server\backend\requirements.txt
.\venv\Scripts\python.exe -m pip install pytest
```

### 配置

编辑 `agent/config/config.py`，填入模型 API Key 与后端地址：

```python
DEEPSEEK_API_KEY = "your-deepseek-api-key"
SERVER_URL = "http://localhost:5000"
```

### 运行

```powershell
cd agent
python flaghunter.py --name "ctfSolver" --challengecode "example" --mode "deepseek"
```

需要后端界面时，先启动 Flask 服务：

```powershell
cd server
docker-compose up -d
```

---

## 测试

这是本仓库相对原版最主要的补充。原版没有可运行的测试，改完之后无法确认是否引入了回归，所以补了一套。

```powershell
.\venv\Scripts\python.exe -m pytest
```

**51 项测试全部通过**，覆盖 9 个文件：

| 测试文件 | 覆盖范围 |
|---|---|
| `tests/conftest.py` | 临时目录、临时 SQLite、公共 fixture |
| `tests/test_imports.py` | 各模块导入完整性 |
| `tests/test_core_framework.py` | 核心框架与任务流转 |
| `tests/test_agent_utils.py` | 智能体工具函数 |
| `tests/test_agent_backend_integration.py` | 智能体与后端联调 |
| `tests/test_actioner_loop.py` | actioner 的调用循环与终止条件 |
| `tests/test_request_addon.py` | HTTP 工具层的异常与超时路径 |
| `tests/test_vuln_modules.py` | 漏洞模块分发 |
| `tests/test_backend_api.py` | Flask 后端 REST 接口 |

几点说明：

- 测试**不需要 API Key、不需要联网**，也不会碰仓库自带的数据库
- 后端用临时 SQLite，智能体用临时目录
- 临时文件统一落在仓库内的 `.pytest-tmp/`（已忽略）。不要改回系统临时目录——受限环境下那里不可写，SQLite 会直接报 `unable to open database file`

---

## 目录结构

```
ctfSolver-master/
├── agent/                    # 智能体核心
│   ├── addons/               # 工具扩展（HTTP / Python / Shell / 解码器）
│   ├── agents/               # 五个智能体与漏洞模块
│   ├── config/               # 配置、POC、Payload、知识库
│   ├── core/                 # 编排器、任务队列、知识库
│   ├── utils/                # 公共工具与 Agent 管理器
│   ├── contest_hunter.py     # 比赛自动化入口
│   ├── flaghunter.py         # 单题解题入口
│   └── requirements.txt
├── server/                   # Flask 后端与前端
├── tests/                    # 9 个测试文件，51 项用例
├── 运行指南.md                # 详细启动与排错步骤
├── 环境说明.md                # 依赖与虚拟环境说明
└── pytest.ini
```

---

## 已知限制

- 只验证过 DeepSeek 模式下的完整链路，腾讯云等其它模式沿用原版实现，未做回归。
- 后端与前端是原版提供的，本仓库只做了运行所需的兼容性修改，没有重做界面。
- 智能体的解题效果依赖模型能力与题目类型，本仓库的改动只保证**链路稳定、错误可回滚、行为可测试**，不保证解题成功率。

---

## 致谢与许可

- 原项目：西安交通大学 xjtuHunter 队伍，腾讯云 AI 渗透智能体黑客松第二名，原维护者九暑（passerW）。
- 本项目沿用原项目的 MIT License 声明。
- 本仓库仅用于 CTF 竞赛、安全教学与授权范围内的研究，请勿在未授权系统上使用。
