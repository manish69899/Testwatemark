# keep_alive.py - Keep the bot alive on hosting platforms
# IMPROVED: Better status page, uptime counter, statistics

import threading
import os
import time
import psutil
from flask import Flask, jsonify

# Track bot start time
BOT_START_TIME = time.time()

app = Flask(__name__)

def get_uptime():
    """Get bot uptime in human readable format"""
    uptime_seconds = int(time.time() - BOT_START_TIME)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    return f"{hours}h {minutes}m {seconds}s"

def get_memory_usage():
    """Get current memory usage in MB"""
    try:
        process = psutil.Process(os.getpid())
        return round(process.memory_info().rss / 1024 / 1024, 1)
    except:
        return 0

def get_cpu_usage():
    """Get CPU usage percentage"""
    try:
        return psutil.cpu_percent(interval=0.1)
    except:
        return 0

@app.route('/')
def home():
    uptime = get_uptime()
    memory = get_memory_usage()
    cpu = get_cpu_usage()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Watermark Bot Status</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}
            .container {{
                text-align: center;
                padding: 40px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 24px;
                backdrop-filter: blur(20px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.1);
                max-width: 600px;
                width: 100%;
            }}
            .logo {{
                font-size: 4em;
                margin-bottom: 10px;
            }}
            h1 {{
                font-size: 2.2em;
                margin-bottom: 8px;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            .subtitle {{
                font-size: 1.1em;
                opacity: 0.8;
                margin-bottom: 25px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin: 25px 0;
            }}
            .stat-card {{
                background: rgba(255, 255, 255, 0.08);
                padding: 20px;
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .stat-icon {{
                font-size: 2em;
                margin-bottom: 8px;
            }}
            .stat-value {{
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .stat-label {{
                font-size: 0.9em;
                opacity: 0.7;
            }}
            .status {{
                display: inline-block;
                padding: 12px 35px;
                background: linear-gradient(90deg, #00b09b 0%, #96c93d 100%);
                border-radius: 30px;
                margin-top: 20px;
                font-weight: bold;
                font-size: 1.1em;
                box-shadow: 0 4px 15px rgba(0, 176, 155, 0.4);
            }}
            .features {{
                margin-top: 25px;
                padding: 20px;
                background: rgba(255, 255, 255, 0.03);
                border-radius: 16px;
            }}
            .features h3 {{
                margin-bottom: 15px;
                opacity: 0.9;
            }}
            .feature-list {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 10px;
            }}
            .feature-tag {{
                background: rgba(102, 126, 234, 0.2);
                padding: 8px 15px;
                border-radius: 20px;
                font-size: 0.85em;
                border: 1px solid rgba(102, 126, 234, 0.3);
            }}
            .footer {{
                margin-top: 25px;
                opacity: 0.6;
                font-size: 0.85em;
            }}
            .pulse {{
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🤖</div>
            <h1>Watermark Bot</h1>
            <p class="subtitle">Advanced PDF Watermark Bot for Telegram</p>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">⏱️</div>
                    <div class="stat-value">{uptime}</div>
                    <div class="stat-label">Uptime</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">💾</div>
                    <div class="stat-value">{memory} MB</div>
                    <div class="stat-label">Memory Usage</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🖥️</div>
                    <div class="stat-value">{cpu}%</div>
                    <div class="stat-label">CPU Usage</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-value">v2.0</div>
                    <div class="stat-label">Bot Version</div>
                </div>
            </div>
            
            <div class="status pulse">✅ ONLINE & RUNNING</div>
            
            <div class="features">
                <h3>✨ Features</h3>
                <div class="feature-list">
                    <span class="feature-tag">📝 Text Watermark</span>
                    <span class="feature-tag">🖼️ Image Watermark</span>
                    <span class="feature-tag">🔤 Custom Fonts</span>
                    <span class="feature-tag">🎨 8 Styles</span>
                    <span class="feature-tag">🔲 20 Borders</span>
                    <span class="feature-tag">🌈 18 Colors</span>
                    <span class="feature-tag">📏 Gap Control</span>
                    <span class="feature-tag">📍 Position</span>
                    <span class="feature-tag">✨ 3D Shadow</span>
                    <span class="feature-tag">🎭 Double Layer</span>
                </div>
            </div>
            
            <div class="footer">
                Made with ❤️ by Aryan & localhost | @hilocalhost
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'bot': 'running',
        'uptime': get_uptime(),
        'memory_mb': get_memory_usage(),
        'cpu_percent': get_cpu_usage(),
        'version': '2.0'
    })

@app.route('/api/stats')
def stats():
    """Detailed stats endpoint"""
    return jsonify({
        'uptime_seconds': int(time.time() - BOT_START_TIME),
        'memory': {
            'used_mb': get_memory_usage(),
            'percent': round(get_memory_usage() / 512 * 100, 1)  # Assuming 512MB limit
        },
        'cpu': {
            'percent': get_cpu_usage()
        },
        'timestamp': int(time.time())
    })

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

def keep_alive():
    """Start the keep-alive server in a background thread"""
    t = threading.Thread(target=run, daemon=True)
    t.start()
    print(f"✅ Keep-alive server started on port {os.environ.get('PORT', 8080)}")

if __name__ == '__main__':
    keep_alive()
    while True:
        time.sleep(1)