import logging
import sys
from datetime import datetime


class UTF8StreamHandler(logging.StreamHandler):
    """确保使用UTF-8编码的StreamHandler，解决Windows中文乱码问题"""
    def __init__(self, stream=None):
        if stream is None:
            stream = sys.stdout
        
        # 在Windows上，如果stream的编码不是UTF-8，创建一个UTF-8包装器
        if hasattr(stream, 'encoding') and stream.encoding and stream.encoding.lower() != 'utf-8':
            from io import TextIOWrapper
            if hasattr(stream, 'buffer'):
                # 使用底层buffer创建UTF-8编码的文本流
                utf8_stream = TextIOWrapper(stream.buffer, encoding='utf-8', errors='replace', line_buffering=True)
                super().__init__(utf8_stream)
            else:
                super().__init__(stream)
        elif hasattr(stream, 'buffer') and (not hasattr(stream, 'encoding') or not stream.encoding):
            # stream没有encoding属性，但有buffer，创建UTF-8包装器
            from io import TextIOWrapper
            utf8_stream = TextIOWrapper(stream.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            super().__init__(utf8_stream)
        else:
            # 已经有UTF-8编码或不需要特殊处理
            super().__init__(stream)
    
    def emit(self, record):
        """发送日志记录，确保UTF-8编码"""
        try:
            msg = self.format(record)
            # 确保消息是字符串
            if isinstance(msg, bytes):
                msg = msg.decode('utf-8', errors='replace')
            
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # 如果遇到编码错误，使用replace策略重新编码
            try:
                msg = self.format(record)
                if isinstance(msg, bytes):
                    msg = msg.decode('utf-8', errors='replace')
                # 确保所有字符都能被正确编码
                msg = msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                stream = self.stream
                stream.write(msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)
        except Exception:
            self.handleError(record)


# 配置日志格式
def setup_logger(log_file=None):
    """
    配置日志系统，确保使用UTF-8编码
    
    Args:
        log_file: 日志文件路径，如果为None则只输出到控制台
    """
    # 自定义日志格式
    log_format = '[%(levelname)s] %(asctime)s [%(name)s:%(filename)s:%(lineno)d] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除已有的处理器，避免重复添加
    logger.handlers.clear()
    
    # 创建控制台处理器，使用UTF-8编码
    console_handler = UTF8StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 设置格式器
    formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器（使用UTF-8编码）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# 获取logger实例
logger = setup_logger()
