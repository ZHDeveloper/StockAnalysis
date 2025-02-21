import logging
import os
import datetime

class Logger:
    def __init__(self):
        self.current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.log_file = None
        self.setup_logger()
    
    def setup_logger(self):
        # 创建logs目录（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # 配置日志格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        self.log_file = f'logs/stock_analysis_{self.current_date}.log'
        
        # 如果日志文件存在，先清空内容
        if os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.truncate(0)
        
        # 配置logging
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def info(self, message):
        logging.info(message)
    
    def error(self, message):
        logging.error(message)
    
    def warning(self, message):
        logging.warning(message)
    
    def debug(self, message):
        logging.debug(message)