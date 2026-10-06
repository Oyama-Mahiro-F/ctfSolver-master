"""导入冒烟测试。

最重要的回归：`utils/chatbot.py` 里的 `from turtle import st` 会拉起 tkinter，
在没有 tkinter 的环境（如 python:3.11-slim）中使整个 agent 无法导入。
"""
import importlib

MODULES = [
    # utils
    "utils.logger",
    "utils.sql_helper",
    "utils.page_helper",
    "utils.task_helper",
    "utils.chatbot",
    "utils.flagUtil",
    "utils.agent_manager",
    "utils.requestUtil",
    # addons
    "addons.request",
    "addons.distinguish",
    "addons.fuzz",
    "addons.jsfuck",
    "addons.base64decode",
    "addons.php_filter_chain",
    "addons.run_python",
    "addons.run_shell",
    # agents
    "agents.explorer",
    "agents.scanner",
    "agents.solutioner",
    "agents.actioner",
    "agents.executor",
    "agents.saver",
    "agents.vulner",
    "agents.poc",
    "agents.vulns.IDOR",
    "agents.vulns.LFI",
    "agents.vulns.OTHER",
    # core（多AI调度框架）
    "core.knowledge_base",
    "core.task_queue",
    "core.orchestrator",
    "core.master_orchestrator",
]


def test_all_agent_modules_import(agent_path):
    for name in MODULES:
        importlib.import_module(name)


def test_core_package_imports(agent_path):
    """回归：core/__init__.py 的 eager 导入曾因 chatbot 的 turtle 依赖整体失败。"""
    importlib.import_module("core")


def test_flaghunter_imports(agent_path):
    """flaghunter 是主入口；它不可导入时整个项目无法运行。"""
    importlib.import_module("flaghunter")
