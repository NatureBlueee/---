# 语音转文字服务

这是一个基于 Flask 的语音转文字服务，支持将演讲/会议录音自动转录为文字，并发送到飞书群组。

## 功能特点

- 支持多种音频格式（mp3, m4a, wav, ogg）
- 自动转录为文字
- 飞书群组通知
- 文件自动清理
- 资源使用优化

## 系统要求

- Python 3.8+
- 2 CPU
- 2GB RAM
- 3MB 带宽

## 安装

1. 克隆仓库：
```bash
git clone [repository_url]
cd speech-to-text-service
```

2. 创建虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 创建配置文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的环境变量：
```
BIBIGPT_API_TOKEN=your_api_token
FEISHU_WEBHOOK_URL=your_webhook_url
UPLOAD_FOLDER=/path/to/upload/folder
DEBUG=False
```

## 运行

开发环境：
```bash
python app.py
```

生产环境：
```bash
gunicorn -w 2 -b 0.0.0.0:5000 'app:init_app()'
```

## 使用方法

1. 访问 `http://your-server:5000`
2. 选择音频文件（支持 mp3, m4a, wav, ogg）
3. 点击上传
4. 等待处理完成
5. 转录结果会显示在页面上，同时发送到配置的飞书群组

## 注意事项

- 最大文件大小限制为 16MB
- 临时文件会在 1 小时后自动清理
- 建议使用 HTTPS 以保护数据传输安全
- 确保服务器有足够的磁盘空间存储临时文件

## 错误处理

常见错误及解决方案：

1. 文件上传失败
   - 检查文件大小是否超过限制
   - 确认文件格式是否支持

2. 转录失败
   - 检查 BibiGPT API Token 是否有效
   - 确认网络连接是否正常

3. 飞书消息发送失败
   - 验证 Webhook URL 是否正确
   - 检查是否超过消息频率限制

## 监控和日志

- 日志文件位置：`logs/app.log`
- 日志轮转：500MB
- 保留时间：10 天

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License 