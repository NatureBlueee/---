import requests
from loguru import logger
from config import Config
from typing import Optional, Dict, Any
import time
import os
import json
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class TranscriptionService:
    def __init__(self):
        self.api_token = Config.BIBIGPT_API_TOKEN
        self.api_base_url = Config.BIBIGPT_API_BASE_URL
        
        # 配置 requests session 以处理重试
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT"]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.timeout = (5, 30)  # (连接超时, 读取超时)
        
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """获取文件元数据"""
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        return {
            "file_size": round(file_size, 2),
            "file_type": os.path.splitext(file_path)[1][1:],
        }

    def upload_to_transfer_sh(self, file_path: str) -> Optional[str]:
        """上传文件到 transfer.sh 获取临时URL"""
        try:
            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                response = self.session.put(
                    f'https://transfer.sh/{filename}', 
                    data=f,
                    headers={'Max-Days': '1'}  # 文件保存1天
                )
                response.raise_for_status()
                return response.text.strip()
        except Exception as e:
            logger.error(f"上传文件失败: {str(e)}")
            return None

    def upload_to_catbox(self, file_path: str) -> Optional[str]:
        """上传文件到 catbox.moe 获取临时URL"""
        try:
            with open(file_path, 'rb') as f:
                files = {'fileToUpload': (os.path.basename(file_path), f)}
                response = self.session.post(
                    'https://catbox.moe/user/api.php',
                    data={'reqtype': 'fileupload'},
                    files=files
                )
                response.raise_for_status()
                url = response.text.strip()
                # 验证返回的是否是有效的URL
                if not url.startswith('http'):
                    raise Exception(f"无效的响应: {url}")
                return url
        except Exception as e:
            logger.error(f"上传文件到 catbox 失败: {str(e)}")
            return None

    def upload_to_temp_sh(self, file_path: str) -> Optional[str]:
        """上传文件到 temp.sh 获取临时URL"""
        try:
            with open(file_path, 'rb') as f:
                response = self.session.post(
                    'https://temp.sh/upload',
                    files={'file': f}
                )
                response.raise_for_status()
                return response.text.strip()
        except Exception as e:
            logger.error(f"上传文件到 temp.sh 失败: {str(e)}")
            return None
        
    def transcribe(self, file_path: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """调用 BibiGPT API 进行转录"""
        try:
            # 尝试不同的文件托管服务
            file_url = None
            for upload_func in [self.upload_to_catbox, self.upload_to_transfer_sh, self.upload_to_temp_sh]:
                file_url = upload_func(file_path)
                if file_url:
                    break
            
            if not file_url:
                raise Exception("无法获取文件的公网访问URL")
            
            logger.info(f"文件已上传，URL: {file_url}")
            
            # 严格按照 BibiGPT 官方调用方式
            url = f"{self.api_base_url}/{self.api_token}/subtitle"
            querystring = {"url": file_url}
            
            logger.info(f"开始转录请求")
            response = requests.request("GET", url, params=querystring)
            response.raise_for_status()
            
            result = response.json()
            if not result.get('success'):
                error_msg = result.get('message') or result.get('error') or '未知错误'
                raise Exception(f"API 处理失败: {error_msg}")
            
            # 提取文本（带时间戳）
            subtitles = result.get('detail', {}).get('subtitlesArray', [])
            text_lines = []
            for sub in subtitles:
                if 'text' in sub:
                    start_time = round(float(sub.get('start', 0)), 1)
                    end_time = round(float(sub.get('end', 0)), 1)
                    text_lines.append(f"[{start_time}s -> {end_time}s] {sub['text']}")
            
            text = '\n'.join(text_lines)
            
            # 计算总时长（假设最后一个字幕的结束时间就是总时长）
            duration = 0
            if subtitles:
                last_subtitle = subtitles[-1]
                if 'end' in last_subtitle:
                    duration = round(float(last_subtitle['end']) / 60, 1)  # 转换为分钟
            
            return {
                'success': True,
                'text': text,
                'duration': duration,
                'raw_subtitles': subtitles  # 保存原始字幕数据，以备后用
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"转录请求失败: {str(e)}")
            if retry_count < Config.MAX_RETRIES:
                logger.info(f"尝试重试 ({retry_count + 1}/{Config.MAX_RETRIES})")
                time.sleep(Config.RETRY_DELAY)
                return self.transcribe(file_path, retry_count + 1)
            return None
            
        except Exception as e:
            logger.error(f"转录处理错误: {str(e)}")
            return None

# 创建单例实例
transcription_service = TranscriptionService() 