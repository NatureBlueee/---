from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
from loguru import logger
import time
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from services.transcription import transcription_service
from services.feishu import feishu_service

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>语音转文字服务</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .upload-form {
            background: white;
            border: 2px dashed #ccc;
            padding: 20px;
            text-align: center;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        input[type="file"] {
            margin: 10px 0;
            padding: 10px;
        }
        input[type="submit"] {
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        input[type="submit"]:hover {
            background: #45a049;
        }
        #result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            white-space: pre-wrap;
        }
        .success { color: #4CAF50; }
        .error { color: #f44336; }
        .loading {
            display: none;
            margin: 20px auto;
            text-align: center;
        }
        .loading.active { display: block; }
    </style>
</head>
<body>
    <div class="upload-form">
        <h2>语音转文字服务</h2>
        <p>支持格式：mp3, m4a, wav, ogg</p>
        <p>最大文件大小：16MB</p>
        <form id="uploadForm">
            <input type="file" name="audio" accept="audio/*" required>
            <br>
            <input type="submit" value="上传并处理">
        </form>
    </div>
    <div id="loading" class="loading">处理中...</div>
    <div id="result"></div>

    <script>
        document.getElementById('uploadForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('input[type="submit"]');
            const loadingDiv = document.getElementById('loading');
            const resultDiv = document.getElementById('result');
            
            if (!formData.get('audio').size) {
                resultDiv.innerHTML = '请选择文件';
                resultDiv.className = 'error';
                return;
            }
            
            try {
                submitButton.disabled = true;
                loadingDiv.className = 'loading active';
                resultDiv.innerHTML = '处理中，请稍候...';
                resultDiv.className = '';
                
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    resultDiv.innerHTML = result.text || '处理完成，但没有识别到文本';
                    resultDiv.className = 'success';
                } else {
                    resultDiv.innerHTML = '错误: ' + (result.error || '未知错误');
                    resultDiv.className = 'error';
                }
            } catch (error) {
                resultDiv.innerHTML = '上传失败: ' + error.message;
                resultDiv.className = 'error';
            } finally {
                submitButton.disabled = false;
                loadingDiv.className = 'loading';
            }
        };
    </script>
</body>
</html>
'''

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def cleanup_old_files():
    """清理超过1小时的临时文件"""
    current_time = time.time()
    for filename in os.listdir(Config.UPLOAD_FOLDER):
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getctime(file_path)
            if file_age > Config.CLEANUP_INTERVAL:
                try:
                    os.remove(file_path)
                    logger.info(f"已清理临时文件: {filename}")
                except Exception as e:
                    logger.error(f"清理文件失败 {filename}: {str(e)}")

@app.route('/')
def index():
    """渲染主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传和转录"""
    try:
        logger.info("开始处理上传请求")
        
        # 验证文件
        if 'audio' not in request.files:
            logger.error("没有文件在请求中")
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        file = request.files['audio']
        if not file or not allowed_file(file.filename):
            logger.error("文件无效或格式不支持")
            return jsonify({'success': False, 'error': '文件无效或格式不支持'}), 400

        # 保存文件
        filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        logger.info(f"文件已保存: {filepath}")
        
        try:
            # 获取文件元数据
            metadata = transcription_service.get_file_metadata(filepath)
            
            # 调用转录服务
            result = transcription_service.transcribe(filepath)
            if not result:
                raise Exception("转录失败")
                
            # 更新元数据
            metadata['duration'] = result['duration']
            
            # 发送到飞书
            formatted_text = feishu_service.format_transcript(result['text'], metadata)
            feishu_service.send_message(formatted_text)
            
            return jsonify({
                'success': True,
                'text': formatted_text
            })

        finally:
            # 清理文件
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"临时文件已删除: {filepath}")

    except Exception as e:
        logger.error(f"处理错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_file(filename):
    """提供临时文件访问"""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

def init_app():
    """初始化应用"""
    # 配置日志
    logger.add("logs/app.log", rotation="500 MB", retention="10 days")
    
    # 启动定时清理任务
    scheduler = BackgroundScheduler()
    scheduler.configure(timezone='Asia/Shanghai')
    scheduler.add_job(cleanup_old_files, 'interval', hours=1)
    scheduler.start()
    
    return app

if __name__ == '__main__':
    try:
        app = init_app()
        logger.info(f"Starting application on {Config.HOST}:{Config.PORT}")
        app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        raise 