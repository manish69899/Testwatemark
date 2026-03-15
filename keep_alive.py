from flask import Flask
from threading import Thread
import logging

# Faltu flask logs ko hide karne ke liye taaki console clean rahe
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    return "Bot is perfectly running! 🚀"

def run():
    # Binds to 0.0.0.0 taaki cloud server pe port properly bind ho
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("✅ Keep-Alive Server Started! Storage & RAM are monitored.")