import os

from flask import Flask
from flask_cors import CORS
from models import db, init_db
from controllers.task_controller import task_bp
from controllers.vuln_controller import vuln_bp
from controllers.page_controller import page_bp
from controllers.agent_controller import agent_bp
from controllers.message_controller import message_bp
from controllers.process_controller import process_bp

app = Flask(__name__)

# 配置数据库
# 允许通过环境变量覆盖（便于测试/多环境部署），默认行为保持不变
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CTF_DATABASE_URI', 'sqlite:///ctf_tasks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Celery配置
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# 启用CORS支持前端跨域请求
# 注意：flask-cors 对每个请求只应用第一个匹配的 path 规则，
# 因此 /api/* 必须自己列出全部允许来源，不能依赖后面的 /* 通配规则。
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173", "http://127.0.0.1:5173",  # vite dev
            "http://localhost:3000", "http://127.0.0.1:3000",
            "http://localhost:85", "http://127.0.0.1:85",       # docker-compose 前端
            "http://localhost:8081", "http://127.0.0.1:8081",   # proxy_server.py
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    },
})

# 初始化Celery
# Celery 是可选依赖：只有使用异步任务时才需要 celery + redis。
# 缺少时后端仍必须能正常提供 REST API，否则按 requirements.txt 安装会直接启动失败。
try:
    from celery_config import make_celery
    celery = make_celery(app)
except Exception as _celery_error:  # pragma: no cover - 取决于运行环境
    celery = None
    print(f"[WARN] Celery 不可用，已跳过异步任务初始化（REST API 不受影响）: {_celery_error}")

# 初始化数据库 - 只调用一次init_db即可
init_db(app)

# 注册蓝图
app.register_blueprint(task_bp)
app.register_blueprint(vuln_bp)
app.register_blueprint(page_bp)
app.register_blueprint(agent_bp)
app.register_blueprint(message_bp)
app.register_blueprint(process_bp)

@app.route('/')
def hello_world():
    return 'CTF Task Management API is running!'

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'API is running'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
