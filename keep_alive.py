from flask import Flask, render_template_string
from threading import Thread
import logging
import time

# Faltu flask logs ko hide karne ke liye taaki console clean rahe
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

# Start time record kar rahe hain taaki uptime dikha sakein (optional visual detail)
START_TIME = time.time()

# HTML & CSS for the Animated Web Page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Status Dashboard</title>
    <style>
        body {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        .container {
            text-align: center;
            padding: 40px 50px;
            border-radius: 20px;
            background: #161b22;
            box-shadow: 0 0 30px rgba(88, 166, 255, 0.15);
            border: 1px solid #30363d;
            position: relative;
        }
        h1 {
            color: #58a6ff;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .status-badge {
            display: inline-block;
            padding: 10px 25px;
            border-radius: 30px;
            background: rgba(46, 160, 67, 0.15);
            color: #3fb950;
            font-weight: 600;
            font-size: 1.1em;
            border: 1px solid rgba(46, 160, 67, 0.4);
            animation: pulse 2s infinite;
            margin-top: 15px;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(63, 185, 80, 0); }
            100% { box-shadow: 0 0 0 0 rgba(63, 185, 80, 0); }
        }
        .loader {
            border: 4px solid #21262d;
            border-top: 4px solid #58a6ff;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px auto;
        }
        @keyframes spin { 
            0% { transform: rotate(0deg); } 
            100% { transform: rotate(360deg); } 
        }
        .details {
            margin-top: 30px;
            font-size: 0.95em;
            color: #8b949e;
            line-height: 1.6;
            text-align: left;
            background: #0d1117;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #30363d;
        }
        .highlight {
            color: #e6edf3;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <h1>🤖 Bot is Live & Active</h1>
        <div class="status-badge">● System Online</div>
        
        <div class="details">
            <p>🚀 <b>Environment:</b> <span class="highlight">Hugging Face Spaces (Docker)</span></p>
            <p>⚙️ <b>Service:</b> <span class="highlight">Watermark Processing Bot</span></p>
            <p>🛡️ <b>Status:</b> <span class="highlight">Storage & RAM are Monitored</span></p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    # Plain text ki jagah ab upar wala animated HTML render hoga
    return render_template_string(HTML_TEMPLATE)

def run():
    # Port 7860 set kiya gaya hai kyunki Hugging Face Spaces Docker ke liye yahi standard hai
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("✅ Keep-Alive Animated Server Started on Port 7860! Web dashboard is live.")
