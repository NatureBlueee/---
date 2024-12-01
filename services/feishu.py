import requests
from loguru import logger
from config import Config
from typing import Optional
import time

class FeishuService:
    def __init__(self):
        self.webhook_url = Config.FEISHU_WEBHOOK_URL
        self.last_send_time = 0
        self.min_interval = 60 / int(Config.RATE_LIMIT.split('/')[0])  # 根据速率限制计算最小间隔
    
    def format_transcript(self, text: str, metadata: Optional[dict] = None) -> str:
        """格式化转录文本，添加元数据"""
        header = "📝 语音转文字结果\n"
        if metadata:
            header += f"🎤 时长：{metadata.get('duration', '未知')}分钟\n"
            header += f"📊 文件大小：{metadata.get('file_size', '未知')}MB\n"
            header += f"📁 文件格式：{metadata.get('file_type', '未知')}\n"
        
        header += "\n🕒 时间戳格式说明：[开始时间s -> 结束时间s]\n"
        
        return f"{header}\n{text}"
    
    def send_message(self, text: str, retry_count: int = 0) -> bool:
        """发送消息到飞书群"""
        if not self.webhook_url:
            logger.warning("飞书 Webhook URL 未配置")
            return False
            
        # 速率限制处理
        current_time = time.time()
        if current_time - self.last_send_time < self.min_interval:
            time.sleep(self.min_interval - (current_time - self.last_send_time))
        
        try:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": text
                }
            }
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            self.last_send_time = time.time()
            logger.info("消息发送成功")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"发送消息失败: {str(e)}")
            if retry_count < Config.MAX_RETRIES:
                logger.info(f"尝试重试 ({retry_count + 1}/{Config.MAX_RETRIES})")
                time.sleep(Config.RETRY_DELAY)
                return self.send_message(text, retry_count + 1)
            return False

# 创建单例实例
feishu_service = FeishuService() 