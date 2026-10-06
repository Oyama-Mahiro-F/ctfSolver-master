#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的HTTP代理服务器，用于将前端API请求转发到后端Flask服务
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import requests
import json

class ProxyHandler(BaseHTTPRequestHandler):
    BACKEND_URL = 'http://localhost:5000'
    
    def do_GET(self):
        """处理GET请求"""
        if self.path.startswith('/api/'):
            # 代理API请求到后端
            self.proxy_request('GET')
        else:
            # 静态文件请求，使用SimpleHTTPRequestHandler的逻辑
            self.serve_static()
    
    def do_POST(self):
        """处理POST请求"""
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            self.send_error(404)
    
    def do_PUT(self):
        """处理PUT请求"""
        if self.path.startswith('/api/'):
            self.proxy_request('PUT')
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        """处理DELETE请求"""
        if self.path.startswith('/api/'):
            self.proxy_request('DELETE')
        else:
            self.send_error(404)

    def do_PATCH(self):
        """处理PATCH请求（前端切换任务运行状态使用）"""
        if self.path.startswith('/api/'):
            self.proxy_request('PATCH')
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        """处理CORS预检请求，否则浏览器会因 501 拦截 PATCH/PUT"""
        if not self.path.startswith('/api/'):
            self.send_error(404)
            return
        origin = self.headers.get('Origin', '*')
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', self.headers.get('Access-Control-Request-Headers', 'Content-Type, Authorization'))
        self.end_headers()

    def proxy_request(self, method):
        """代理请求到后端"""
        try:
            url = f"{self.BACKEND_URL}{self.path}"
            headers = dict(self.headers)
            
            # 移除Host头，避免冲突
            if 'Host' in headers:
                del headers['Host']
            
            # 读取请求体（如果有）
            content_length = int(headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # 发送请求到后端
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                timeout=30
            )
            
            # 返回响应
            self.send_response(response.status_code)
            
            # 复制响应头。
            # requests 会自动解压 gzip，若原样透传 Content-Encoding/Content-Length，
            # 客户端会按压缩数据的长度解析已解压的内容而出错，因此这里剔除后重新计算长度。
            for key, value in response.headers.items():
                if key.lower() not in ['connection', 'transfer-encoding', 'content-encoding', 'content-length']:
                    self.send_header(key, value)

            self.send_header('Content-Length', str(len(response.content)))
            self.end_headers()
            self.wfile.write(response.content)
            
        except requests.exceptions.ConnectionError:
            self.send_error(502, "Cannot connect to backend service")
        except Exception as e:
            # Use ASCII-safe error message to avoid encoding issues
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            self.send_error(500, f"Proxy error: {error_msg}")
    
    def serve_static(self):
        """提供静态文件服务"""
        import os
        from pathlib import Path
        
        # 获取前端dist目录
        dist_dir = Path(__file__).parent / 'dist'
        
        # 处理路径
        path = self.path
        if path == '/':
            path = '/index.html'
        
        file_path = dist_dir / path.lstrip('/')
        
        # 检查文件是否存在
        if file_path.exists() and file_path.is_file():
            # 确定Content-Type
            content_type = self.guess_type(str(file_path))
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            # 对于SPA，所有路由都返回index.html
            index_file = dist_dir / 'index.html'
            if index_file.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                with open(index_file, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
    
    def guess_type(self, path):
        """猜测文件类型"""
        import mimetypes
        mimetype, _ = mimetypes.guess_type(path)
        return mimetype or 'application/octet-stream'
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run(port=8081):
    """启动代理服务器"""
    import socket
    # 检查端口是否可用
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('', port))
        sock.close()
    except OSError:
        print(f"端口 {port} 已被占用，尝试使用 8082...")
        port = 8082
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
        except OSError:
            print(f"端口 {port} 也被占用，请手动指定端口")
            return
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, ProxyHandler)
    print(f"前端代理服务器启动在 http://localhost:{port}")
    print(f"API请求将被代理到 {ProxyHandler.BACKEND_URL}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器关闭")
        httpd.shutdown()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    run(port)
