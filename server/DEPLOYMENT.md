# Server端部署说明

Server端提供Flask后端API和前端界面，用于管理CTF任务和Agent。

## 部署方式

### 方式一：Docker部署（推荐）

**前提条件**：
- 已安装Docker和Docker Compose
- 需要先构建Docker镜像

**步骤**：

1. 构建后端镜像：
```bash
cd server/backend
docker build -t ctfui-backend:latest .
```

2. 构建前端镜像（如果有前端源码）：
```bash
cd server/frontend
docker build -t ctfui-frontend:latest .
```

3. 启动服务：
```bash
cd server
docker-compose up -d
```

4. 访问服务：
- 前端界面: http://localhost:85
- 后端API: http://localhost:5000

### 方式二：本地运行后端

**前提条件**：
- Python 3.8+
- 已安装Redis（用于Celery，可选）

**步骤**：

1. 安装依赖：
```bash
cd server/backend
pip install -r requirements.txt
```

2. 安装Celery和Redis（如果需要异步任务）：
```bash
pip install celery redis
```

3. 启动Redis（如果使用Celery）：
```bash
# Windows: 下载Redis for Windows或使用WSL
# Linux/Mac: redis-server
```

4. 运行Flask应用：
```bash
python app.py
```

5. 访问API：
- API地址: http://localhost:5000
- 健康检查: http://localhost:5000/health

## 注意事项

1. **Redis依赖**：如果使用Celery进行异步任务处理，需要安装并运行Redis
2. **端口占用**：确保5000和85端口未被占用
3. **数据库**：后端使用SQLite数据库，会自动创建在`server/backend/instance/ctf_tasks.db`
4. **CORS**：后端已配置CORS，支持跨域请求

## API端点

主要API端点：
- `GET /api/agents` - 获取Agent列表
- `POST /api/agents/register` - 注册Agent
- `POST /api/agents/{id}/heartbeat` - Agent心跳
- `GET /api/tasks` - 获取任务列表
- `POST /api/tasks` - 创建任务
- `GET /api/tasks/{id}` - 获取任务详情

## 故障排查

- **端口被占用**：修改`app.py`中的端口号或`docker-compose.yaml`中的端口映射
- **Redis连接失败**：如果不使用Celery，可以注释掉相关配置
- **数据库错误**：删除`instance/ctf_tasks.db`重新初始化
