import logging
import os
import datetime

class Logger:
    def __init__(self):
        self.log_file = None
        self.handlers = []
        self.setup_logger()
    
    def setup_logger(self):
        # 创建logs目录（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # 配置日志格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        self.log_file = 'logs/stock_analysis.log'
        
        # 如果日志文件存在，先清空内容
        if os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.truncate(0)
        
        # 配置logging
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        stream_handler = logging.StreamHandler()
        self.handlers = [file_handler, stream_handler]
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=self.handlers
        )
    
    def __del__(self):
        # 在对象被销毁时关闭所有处理器
        for handler in self.handlers:
            handler.close()
            logging.getLogger().removeHandler(handler)
    
    def info(self, message):
        logging.info(message)
    
    def error(self, message):
        logging.error(message)
    
    def warning(self, message):
        logging.warning(message)
    
    def debug(self, message):
        logging.debug(message)