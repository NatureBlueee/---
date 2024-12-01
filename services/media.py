import os
from loguru import logger
import subprocess
from typing import Optional
import uuid

class MediaService:
    def __init__(self):
        self.temp_dir = os.getenv('UPLOAD_FOLDER', '/tmp/audio_uploads')
        os.makedirs(self.temp_dir, exist_ok=True)

    def is_video_file(self, filename: str) -> bool:
        """检查是否是视频文件"""
        video_extensions = {'mp4', 'mov', 'avi', 'mkv'}
        return filename.rsplit('.', 1)[1].lower() in video_extensions

    def extract_audio(self, video_path: str) -> Optional[str]:
        """从视频文件中提取音频"""
        try:
            # 生成临时音频文件路径
            audio_filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(self.temp_dir, audio_filename)

            # 使用 ffmpeg 提取音频
            command = [
                'ffmpeg',
                '-i', video_path,  # 输入文件
                '-vn',  # 禁用视频
                '-acodec', 'libmp3lame',  # 使用 MP3 编码器
                '-ar', '44100',  # 采样率
                '-ab', '192k',  # 比特率
                '-y',  # 覆盖输出文件
                audio_path
            ]

            # 执行命令
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logger.error(f"音频提取失败: {stderr.decode()}")
                return None

            logger.info(f"音频提取成功: {audio_path}")
            return audio_path

        except Exception as e:
            logger.error(f"音频提取过程出错: {str(e)}")
            return None

    def cleanup_file(self, file_path: str):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"临时文件已删除: {file_path}")
        except Exception as e:
            logger.error(f"清理文件失败 {file_path}: {str(e)}")

# 创建单例实例
media_service = MediaService() 