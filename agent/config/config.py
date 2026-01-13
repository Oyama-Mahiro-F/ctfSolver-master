import os
import random
import sqlite3
import uuid

from utils.logger import logger

API_KEYS = []

# ============================================
# LLM API 配置说明
# ============================================
# 请至少配置一个LLM API密钥才能运行Agent
# 支持的API服务：
# 1. DeepSeek (推荐): https://platform.deepseek.com/
# 2. 腾讯云: https://cloud.tencent.com/
# 3. SiliconFlow: https://siliconflow.cn/
# 4. GLM (智谱AI): https://open.bigmodel.cn/
# ============================================

DEEPSEEK_API_URL = "https://api.deepseek.com"
DEEPSEEK_API_KEY = "sk-676280974f6b4fa58de1c6d79e0f193c"  # 请在此处填入您的DeepSeek API密钥
DEEPSEEK_API_MODEL_ACTION = "deepseek-chat"

TENCENT_API_URL = "https://api.lkeap.cloud.tencent.com/v1"
TENCENT_API_KEY = ""  # 请在此处填入您的腾讯云API密钥
TENCENT_API_MODEL_ACTION = "deepseek-v3.1-terminus"
TENCENT_API_RANDOM_KEY = random.choice(API_KEYS) if API_KEYS else ""


SILCON_API_URL = "https://api.siliconflow.cn/v1"
SILCON_API_KEY = ""  # 请在此处填入您的SiliconFlow API密钥
SILCON_API_MODEL_ACTION = "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"

# API配置
API_URL = "https://api.deepseek.com"
API_KEY = ""  # 通用API密钥配置
API_MODEL_ACTION = "deepseek-chat"

CONTEST_API_TOKEN = ""  # 比赛API令牌（如果参与比赛）

GLM_URL = "https://open.bigmodel.cn/api/paas/v4"
GLM_API_KEY = ""  # 请在此处填入您的GLM API密钥
GLM_MODEL = "glm-4-long"

NAME = "ctfSolver"
CHALLENGE_CODE = ""

# Server配置
SERVER_URL = "http://localhost:5000"  # 后端服务器地址（如果使用本地server，使用localhost；如果使用远程server，请修改为对应地址）
AGENT_VERSION = "1.0.0"  # Agent版本
HEARTBEAT_INTERVAL = 30  # 心跳间隔（秒）
AGENT_CAPABILITIES = ["web_scan", "vuln_detect", "flag_search", "page_explore"]  # Agent能力

# SQLite数据库配置
BASE_PATH = str(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_PATH, "chat.db")
INIT_SQL = os.path.join(BASE_PATH, "init.sql")
ADDON_README_PATH = os.path.join(BASE_PATH, "addons.txt")
TEMP_PATH = os.path.join(BASE_PATH, "temp/")

POC_PATH = os.path.join(BASE_PATH, "pocs/")

BASE_URL = "http://10.0.0.6:8000"

HUNTER = None

FORMS = {}

EXPLORE_URLS = []

# CTF任务配置
CTF_URL = ""
CTF_DESC = ""
TARGET = ""  # 添加TARGET配置
DESCRIPTION = ""  # 添加DESCRIPTION配置
TASK_PATH = os.path.join(os.path.dirname(BASE_PATH), "tasks")  # 任务存储路径

# ============================================
# DVWA (Damn Vulnerable Web Application) 配置说明
# ============================================
# DVWA是一个用于安全测试和训练的Web应用程序，包含多种常见Web漏洞
# 
# 部署方式：
# 1. Docker部署（推荐）：
#    docker run --rm -it -p 80:80 vulnerables/web-dvwa
#    访问地址：http://localhost
# 
# 2. 本地安装：
#    需要PHP、MySQL、Apache环境
#    下载地址：https://github.com/digininja/DVWA
#    常见部署路径：http://localhost/dvwa 或 http://127.0.0.1/dvwa
# 
# 3. 使用docker-compose：
#    参考官方文档配置docker-compose.yaml
# 
# 安全级别说明：
# - low: 最低安全级别，漏洞利用最简单，适合初学者
# - medium: 中等安全级别，有一定防护措施
# - high: 高安全级别，防护措施较强
# - impossible: 最高安全级别，漏洞已修复
# 
# 使用方式：
# 1. 直接使用：设置 CTF_URL = DVWA_URL 或 TARGET = DVWA_URL
# 2. 命令行：python flaghunter.py --url <DVWA_URL>
# 3. 任务API：通过任务创建接口传入DVWA URL
# ============================================

# DVWA配置
DVWA_URL = "http://localhost/dvwa"  # DVWA部署地址（根据实际部署修改）
# 常见DVWA部署地址示例：
# - http://localhost/dvwa
# - http://127.0.0.1/dvwa
# - http://localhost:80 (Docker默认端口)
# - http://your-ip:port/dvwa (远程部署)
DVWA_SECURITY_LEVEL = "low"  # 安全级别：low, medium, high, impossible
DVWA_USERNAME = "admin"  # DVWA登录用户名（默认：admin）
DVWA_PASSWORD = "password"  # DVWA登录密码（默认：password）

MAX_COUNT = 4
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "key.txt")
ADDON_PATH = os.path.join(BASE_PATH, "addons/")
KNOWLEGDE_PATH = os.path.join(BASE_PATH, "knowledge/")
PAYLOAD_PATH = os.path.join(BASE_PATH, "payload/")

# Agent相关配置
AGENT_ID = None  # 将在注册时获得
AGENT_STATUS = "idle"  # Agent状态：idle, running, error, exploring, detecting

TASK_ID = ""
EXPLORED_PAGES = []
EXPLORED_PAGE_RESPONSES = []
NEED_FLAG = False
FLAG = ""
IGNORE_STATUS_LIST = [404, 405]
WRONG_STATUS_LIST = [405]

XRAY_PROXY = "127.0.0.1:7783"
XRAY_CMD = f"cd {BASE_PATH} && ./xray webscan --listen {XRAY_PROXY} --json-output #result_file#"
PYTHON_CMD = "python3"

messages = []


# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 读取SQL文件并按分号分割为单独的语句
    with open(INIT_SQL, "r") as sql_file:
        sql_statements = sql_file.read().split(';')

    # 执行每个非空SQL语句
    for statement in sql_statements:
        if statement.strip():
            cursor.execute(statement)

    conn.commit()
    conn.close()
    logger.info(f"数据库已初始化，路径：{DB_PATH}")


def flush_key():
    open(KEY_FILE, "w").close()


def write_key(key):
    with open(KEY_FILE, "a") as f:
        f.write(key + "\n")


def read_keys():
    if not os.path.exists(KEY_FILE):
        flush_key()
    with open(KEY_FILE, "r", encoding='utf-8') as f:
        return f.read()


def get_addon(tool):
    with open(f"{ADDON_PATH}/{tool}.txt", 'r', encoding='utf-8') as f:
        return f.read()


def get_knowledge(knowledge):
    knowledge_base_path = f"{KNOWLEGDE_PATH}/{knowledge}"

    knowledge_files = []
    # 遍历knowledge目录下的所有文件
    for filename in os.listdir(knowledge_base_path):
        file_path = os.path.join(knowledge_base_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                first_line = lines[0] if lines else ''

                # 为每个文件生成唯一ID
                file_id = str(uuid.uuid4())
                knowledge_files.append({
                    "id": file_id,
                    "desc": first_line,
                    "all": content
                })
    return knowledge_files


def get_payload(payload_type):
    payload_file = f"{PAYLOAD_PATH}/{payload_type.lower()}.txt"
    if os.path.exists(payload_file):
        with open(payload_file, "r", encoding='utf-8') as f:
            return f.read().split("\n")
    return []


