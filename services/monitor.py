import os
import sys
import psutil
import time
from loguru import logger
from typing import Dict, Any
import threading

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from config import Config

class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()
        self._monitoring = False
        self._lock = threading.Lock()
        self.stats = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'memory_used': 0,
            'disk_usage': 0,
            'processing_count': 0
        }
        
    def start_monitoring(self):
        """开始监控系统资源"""
        with self._lock:
            if not self._monitoring:
                self._monitoring = True
                thread = threading.Thread(target=self._monitor_resources)
                thread.daemon = True
                thread.start()
                logger.info("系统资源监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        with self._lock:
            self._monitoring = False

    def _monitor_resources(self):
        """持续监控系统资源"""
        while self._monitoring:
            try:
                # CPU 使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # 内存使用情况
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used = memory.used / (1024 * 1024)  # MB
                
                # 磁盘使用情况
                disk = psutil.disk_usage(Config.UPLOAD_FOLDER)
                disk_percent = disk.percent

                with self._lock:
                    self.stats.update({
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_percent,
                        'memory_used': round(memory_used, 2),
                        'disk_usage': disk_percent
                    })

                # 检查是否超过资源限制
                if cpu_percent > 80 or memory_percent > 80:
                    logger.warning(f"系统资源使用率过高: CPU {cpu_percent}%, 内存 {memory_percent}%")

            except Exception as e:
                logger.error(f"监控资源时出错: {str(e)}")
            
            time.sleep(2)  # 每2秒更新一次

    def get_stats(self) -> Dict[str, Any]:
        """获取当前系统状态"""
        with self._lock:
            stats = self.stats.copy()
        
        # 添加运行时间
        uptime = time.time() - self.start_time
        stats['uptime'] = round(uptime, 2)
        
        return stats

    def increment_processing_count(self):
        """增加处理计数"""
        with self._lock:
            self.stats['processing_count'] += 1

    def decrement_processing_count(self):
        """减少处理计数"""
        with self._lock:
            self.stats['processing_count'] = max(0, self.stats['processing_count'] - 1)

# 创建单例实例
system_monitor = SystemMonitor()

# 如果直接运行此文件，执行测试代码
if __name__ == '__main__':
    # 配置日志
    logger.add("monitor.log", rotation="500 MB", retention="10 days")
    
    try:
        print("开始系统监控测试...")
        system_monitor.start_monitoring()
        
        # 持续显示系统状态
        while True:
            stats = system_monitor.get_stats()
            os.system('cls' if os.name == 'nt' else 'clear')  # 清屏
            print("\n当前系统状态:")
            print("-" * 40)
            print(f"CPU 使用率: {stats['cpu_percent']}%")
            print(f"内存使用率: {stats['memory_percent']}%")
            print(f"内存使用量: {stats['memory_used']} MB")
            print(f"磁盘使用率: {stats['disk_usage']}%")
            print(f"运行时间: {stats['uptime']} 秒")
            print(f"处理任务数: {stats['processing_count']}")
            print("-" * 40)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n停止监控...")
        system_monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"监控测试出错: {str(e)}")
    finally:
        print("监控已结束") 