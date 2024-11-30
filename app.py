from flask import Flask, request, jsonify, render_template_string
import os
import uuid
import requests
import logging
from cloudinary.uploader import upload
import cloudinary
import cloudinary.api

app = Flask(__name__)

# Cloudinary 配置
cloudinary.config(
    cloud_name = "dqorxv14a",    # 替换为您的 cloud_name
    api_key = "476965271365468",          # 替换为您的 api_key
    api_secret = "2UH_prz8bbabGneljKKWdy_QJgc"     # 替换为您的 api_secret
)

# API 配置
API_TOKEN = "xyqEM8MtuKtG"  # 您的 API token
API_BASE_URL = "https://bibigpt.co/api/open"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>音频上传</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 500px;
            margin: 20px auto;
            padding: 20px;
        }
        .upload-form {
            border: 2px dashed #ccc;
            padding: 20px;
            text-align: center;
            border-radius: 8px;
        }
        input[type="file"] {
            margin: 10px 0;
        }
        input[type="submit"] {
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        #result {
            margin-top: 20px;
            padding: 10px;
            border-radius: 4px;
            white-space: pre-wrap;
        }
        .success {
            background: #e8f5e9;
            color: #2e7d32;
        }
        .error {
            background: #ffebee;
            color: #c62828;
        }
        .processing {
            background: #e3f2fd;
            color: #1565c0;
        }
    </style>
</head>
<body>
    <div class="upload-form">
        <h2>音频上传处理</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="audio" accept="audio/*" required>
            <br>
            <input type="submit" value="上传并处理">
        </form>
    </div>
    <div id="result"></div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': '没有文件'}), 400
        
        file = request.files['audio']
        if not file:
            return jsonify({'error': '文件无效'}), 400

        try:
            # 上传到 Cloudinary
            logger.info("Uploading to Cloudinary...")
            upload_result = upload(file, 
                                 resource_type="auto",
                                 folder="audio_uploads")
            
            file_url = upload_result['secure_url']
            logger.info(f"File uploaded: {file_url}")

            # 调用转写 API
            api_url = f"{API_BASE_URL}/{API_TOKEN}/subtitle"
            params = {'url': file_url}
            
            logger.info(f"Calling API: {api_url}")
            response = requests.get(api_url, params=params)
            logger.info(f"API Response: {response.text}")
            
            result = response.json()

            if not result.get('success'):
                raise Exception(f"API 处理失败: {result.get('error', '未知错误')}")

            # 提取文本
            subtitles = result.get('detail', {}).get('subtitlesArray', [])
            text = '\n'.join([sub['text'] for sub in subtitles if 'text' in sub])

            return jsonify({
                'success': True,
                'text': text
            })

        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 