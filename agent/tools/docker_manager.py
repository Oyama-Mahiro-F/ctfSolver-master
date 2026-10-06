"""
Docker沙箱管理 - 管理工具在Docker容器中的执行
"""
import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional

from utils.logger import logger

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("docker库未安装，Docker功能将不可用")


class DockerManager:
    """Docker容器管理器"""
    
    def __init__(self, image: str = "python:3.11-slim", network_mode: str = "bridge"):
        """
        初始化Docker管理器
        
        Args:
            image: Docker镜像名称
            network_mode: 网络模式（bridge, host, none）
        """
        self.image = image
        self.network_mode = network_mode
        self.client = None
        self.containers: Dict[str, Any] = {}
        
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
                logger.info("Docker客户端初始化成功")
            except Exception as e:
                logger.error(f"Docker客户端初始化失败: {e}")
                self.client = None
        else:
            logger.warning("Docker不可用，将使用本地执行模式")
    
    def is_available(self) -> bool:
        """检查Docker是否可用"""
        if not DOCKER_AVAILABLE:
            return False
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False
    
    def create_container(self, 
                        container_name: str,
                        command: str,
                        volumes: Optional[Dict[str, Dict]] = None,
                        environment: Optional[Dict[str, str]] = None,
                        cpu_limit: float = 1.0,
                        memory_limit: str = "512m",
                        network_disabled: bool = False) -> Optional[str]:
        """
        创建Docker容器
        
        Args:
            container_name: 容器名称
            command: 要执行的命令
            volumes: 卷映射
            environment: 环境变量
            cpu_limit: CPU限制（0.0-1.0）
            memory_limit: 内存限制（如 "512m", "1g"）
            network_disabled: 是否禁用网络
            
        Returns:
            str: 容器ID，失败返回None
        """
        if not self.is_available():
            logger.error("Docker不可用，无法创建容器")
            return None
        
        try:
            # 准备容器配置
            container_config = {
                "image": self.image,
                "command": command,
                "detach": True,
                "name": container_name,
                "cpu_period": 100000,
                "cpu_quota": int(cpu_limit * 100000),
                "mem_limit": memory_limit,
                "network_disabled": network_disabled,
                "auto_remove": True,  # 自动删除容器
            }
            
            if volumes:
                container_config["volumes"] = volumes
            
            if environment:
                container_config["environment"] = environment
            
            if self.network_mode:
                container_config["network_mode"] = self.network_mode
            
            # 创建容器
            container = self.client.containers.create(**container_config)
            self.containers[container_name] = container
            logger.info(f"创建容器: {container_name} (ID: {container.id[:12]})")
            return container.id
        
        except Exception as e:
            logger.error(f"创建容器失败: {e}")
            return None
    
    def start_container(self, container_name: str) -> bool:
        """启动容器"""
        if container_name not in self.containers:
            logger.error(f"容器不存在: {container_name}")
            return False
        
        try:
            container = self.containers[container_name]
            container.start()
            logger.info(f"启动容器: {container_name}")
            return True
        except Exception as e:
            logger.error(f"启动容器失败: {e}")
            return False
    
    def stop_container(self, container_name: str, timeout: int = 10) -> bool:
        """停止容器"""
        if container_name not in self.containers:
            logger.error(f"容器不存在: {container_name}")
            return False
        
        try:
            container = self.containers[container_name]
            container.stop(timeout=timeout)
            logger.info(f"停止容器: {container_name}")
            return True
        except Exception as e:
            logger.error(f"停止容器失败: {e}")
            return False
    
    def remove_container(self, container_name: str) -> bool:
        """删除容器"""
        if container_name not in self.containers:
            return False
        
        try:
            container = self.containers[container_name]
            container.remove(force=True)
            del self.containers[container_name]
            logger.info(f"删除容器: {container_name}")
            return True
        except Exception as e:
            logger.error(f"删除容器失败: {e}")
            return False
    
    def execute_in_container(self,
                            container_name: str,
                            command: str,
                            timeout: int = 300,
                            workdir: Optional[str] = None) -> tuple[bool, str, str]:
        """
        在容器中执行命令
        
        Args:
            container_name: 容器名称
            command: 要执行的命令
            timeout: 超时时间（秒）
            workdir: 工作目录
            
        Returns:
            tuple: (是否成功, stdout, stderr)
        """
        if not self.is_available():
            return False, "", "Docker不可用"
        
        if container_name not in self.containers:
            # 尝试创建并启动临时容器。
            # create_container 内部只调用 containers.create()，不会启动容器，
            # 若不 start 就 exec，执行必然失败。
            temp_name = f"temp_{int(time.time())}"
            container_id = self.create_container(temp_name, command)
            if not container_id:
                return False, "", "无法创建容器"
            if not self.start_container(temp_name):
                return False, "", "无法启动容器"
            container_name = temp_name
        
        try:
            container = self.containers[container_name]
            
            # 执行命令。
            # 注意：docker-py 的 exec_run() 没有 timeout 参数，传入会直接 TypeError，
            # 因此这里不再传递（超时需由调用方或工具自身控制）。
            exec_result = container.exec_run(
                command,
                workdir=workdir
            )
            
            stdout = exec_result.output.decode('utf-8', errors='ignore') if exec_result.output else ""
            exit_code = exec_result.exit_code
            
            # 如果是临时容器，执行后删除
            if container_name.startswith("temp_"):
                self.remove_container(container_name)
            
            return exit_code == 0, stdout, ""
        
        except Exception as e:
            logger.error(f"在容器中执行命令失败: {e}")
            return False, "", str(e)
    
    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """获取容器日志"""
        if container_name not in self.containers:
            return ""
        
        try:
            container = self.containers[container_name]
            logs = container.logs(tail=tail).decode('utf-8', errors='ignore')
            return logs
        except Exception as e:
            logger.error(f"获取容器日志失败: {e}")
            return ""
    
    def cleanup_all(self):
        """清理所有容器"""
        for container_name in list(self.containers.keys()):
            self.remove_container(container_name)
        logger.info("清理所有容器完成")
    
    def __del__(self):
        """析构函数，清理资源"""
        if hasattr(self, 'containers'):
            self.cleanup_all()
