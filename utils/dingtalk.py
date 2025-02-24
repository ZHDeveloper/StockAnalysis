import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
from utils.logger import Logger

class DingTalkBot:
    # 默认的钉钉机器人配置
    DEFAULT_ACCESS_TOKEN = "c4c9c26fa56f416d5dd9181c3ebe8da6ea8453f2c51d3199ce62a1d62108b314"
    DEFAULT_SECRET = "SEC8d81304eae6789fec96739e6a77ae6e330eceb89a3a03ef9608db30ecd213669"
    
    def __init__(self, access_token=None, secret=None):
        self.access_token = access_token or self.DEFAULT_ACCESS_TOKEN
        self.secret = secret or self.DEFAULT_SECRET
        self.webhook_base_url = "https://oapi.dingtalk.com/robot/send"
        self.logger = Logger()
    
    def _generate_sign(self):
        """生成钉钉机器人签名"""
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign
    
    def _get_webhook_url(self):
        """获取完整的webhook URL"""
        timestamp, sign = self._generate_sign()
        return f"{self.webhook_base_url}?access_token={self.access_token}&timestamp={timestamp}&sign={sign}"
    
    def send_text_message(self, message):
        """发送文本消息
        
        Args:
            message: 要发送的文本消息
            
        Returns:
            bool: 消息发送是否成功
        """
        try:
            webhook_url = self._get_webhook_url()
            headers = {'Content-Type': 'application/json'}
            data = {
                "msgtype": "text",
                "text": {"content": message}
            }
            
            response = requests.post(webhook_url, headers=headers, json=data)
            if response.status_code == 200:
                self.logger.info("钉钉消息发送成功")
                return True
            else:
                self.logger.error(f"钉钉消息发送失败，状态码：{response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"发送钉钉消息时发生错误：{str(e)}")
            return False