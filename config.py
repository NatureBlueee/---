import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # API配置
    BIBIGPT_API_TOKEN = os.getenv('BIBIGPT_API_TOKEN', 'xyqEM8MtuKtG')
    BIBIGPT_API_BASE_URL = os.getenv('BIBIGPT_API_BASE_URL', 'https://bibigpt.co/api/open')
    
    # 飞书配置
    FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', '')
    
    # 文件配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/audio_uploads')
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB，针对音频文件优化
    ALLOWED_EXTENSIONS = {'mp3', 'm4a', 'wav', 'ogg'}  # 只保留音频格式
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # 任务配置
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    CLEANUP_INTERVAL = 3600  # 1 hour
    
    # 资源限制
    MAX_WORKERS = 2  # 基于服务器配置（2 CPU）
    RATE_LIMIT = "20/minute"  # 飞书消息限制