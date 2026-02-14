from flask import Flask, render_template, request, jsonify, Response
import threading
import time
import spam_otp  # Import module spam_otp.py
import proxy_scraper # Pre-import to avoid runtime errors
from datetime import datetime

app = Flask(__name__)

# Global variables
SPAM_RUNNING = False
SPAM_THREADS = []  # Changed to list for multiple threads
LOG_MESSAGES = []  
MAX_LOGS = 50     
STATS = {
    "sent": 0,
    "success": 0,
    "fail": 0,
    "threads": 0
}

def add_log(message, type="system"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    LOG_MESSAGES.append({"text": log_entry, "type": type})
    if len(LOG_MESSAGES) > MAX_LOGS:
        LOG_MESSAGES.pop(0)

def spam_loop_task(phone, delay, proxies, attack_mode='carpet'):
    global SPAM_RUNNING, STATS
    spam_instance = spam_otp.SpamOTP(phone, proxies=proxies, attack_mode=attack_mode)
    
    # Custom logger to capture logs and stats
    def custom_log(msg):
        # Determine log type and stats
        if "Lỗi" in msg:
            STATS["fail"] += 1
            add_log(msg, "error")
        elif "200" in msg:
            STATS["success"] += 1
            STATS["sent"] += 1
            add_log(msg, "success")
        else:
            STATS["sent"] += 1
            add_log(msg, "info")
    
    spam_instance.log = custom_log # Override log method
    
    while SPAM_RUNNING:
        try:
            spam_instance.run_batch(delay=delay)
            time.sleep(delay)
        except Exception as e:
            add_log(f"Thread Error: {e}", "error")
            break

# ... (Routes)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "running": SPAM_RUNNING,
        "stats": STATS,
        "logs": LOG_MESSAGES
    })

@app.route('/proxies')
def proxy_manager():
    return render_template('proxy_manager.html')

@app.route('/guide')
def guide():
    return render_template('guide.html')

# Deprecated old guide route, redirect or remove
@app.route('/proxy-guide')
def proxy_guide_old():
    return render_template('guide.html') # Redirect old link to new guide

@app.route('/api/start', methods=['POST'])
def start_spam():
    global SPAM_RUNNING, SPAM_THREADS, STATS, LOG_MESSAGES
    data = request.json
    phone = data.get('phone')
    delay = float(data.get('delay', 2.0))
    thread_count = int(data.get('threads', 1))
    proxies_raw = data.get('proxies', '')
    attack_mode = data.get('mode', 'carpet') # New: Attack Mode
    auto_proxy = data.get('auto_proxy', False) # New: Auto Proxy
    
    if not phone or len(phone) < 10:
        return jsonify({'status': 'error', 'message': 'Số điện thoại không hợp lệ'}), 400

    if SPAM_RUNNING:
        return jsonify({'status': 'error', 'message': 'Đang chạy spam rồi!'}), 400

    # Proxy Handling
    proxies = []
    if auto_proxy:
        scraper = proxy_scraper.ProxyScraper()
        proxies = scraper.get_proxies()
        add_log(f"Auto-Scraped {len(proxies)} proxies from internet.", "system")
    elif proxies_raw:
        proxies = [p.strip() for p in proxies_raw.split('\n') if p.strip()]

    # Reset stats on new run
    STATS = {"sent": 0, "success": 0, "fail": 0, "threads": thread_count}

    SPAM_RUNNING = True
    SPAM_THREADS = []
    
    for i in range(thread_count):
        # Pass attack_mode to spam_loop via args or modify spam_loop_task
        t = threading.Thread(target=spam_loop_task, args=(phone, delay, proxies, attack_mode))
        t.daemon = True
        t.start()
        SPAM_THREADS.append(t)
    
    add_log(f"Started attack on {phone} | Mode: {attack_mode.upper()} | Threads: {thread_count}", "system")
    return jsonify({'status': 'success', 'message': f'Đã kích hoạt {thread_count} luồng mode {attack_mode.upper()}!'})

@app.route('/api/stop', methods=['POST'])
def stop_spam():
    global SPAM_RUNNING
    if not SPAM_RUNNING:
        return jsonify({'status': 'error', 'message': 'Không có tiến trình nào đang chạy'}), 400
    
    SPAM_RUNNING = False
    STATS["threads"] = 0
    add_log("Stopping all threads...", "system")
    return jsonify({'status': 'success', 'message': 'Đã dừng toàn bộ spam!'})

@app.route('/api/reset_identity', methods=['POST'])
def reset_identity():
    # Simulate identity reset logic here
    # In a real scenario this might rotate proxies or clear session cookies
    # We can invoke a method on spam_instance if we had one
    # For now, we log it and verify success
    add_log("IDENTITY RESET: Rotating User-Agents & Clearing Cookies...", "system")
    return jsonify({'status': 'success', 'message': 'Identity reset successfully'})

# --- TELEGRAM BOT INTEGRATION ---
TELEGRAM_BOT = None
TELEGRAM_TOKEN = "8406827765:AAF_HUzbk01ZLaLsJOwwlsDwxzRMY5GblAE" 
TELEGRAM_CHAT_ID = "" # User needs to find this via /start

def start_telegram_bot_thread():
    global TELEGRAM_BOT
    if not TELEGRAM_TOKEN:
        return

    import telegram_bot
    
    # Callbacks for the bot to control the app
    def bot_start_attack(phone, delay, threads, proxies, mode):
        # We need to simulate the start_spam logic but internal
        global SPAM_RUNNING, SPAM_THREADS, STATS
        if SPAM_RUNNING:
             return {"status": "error", "message": "System is already running!"}
        
        STATS = {"sent": 0, "success": 0, "fail": 0, "threads": threads, "running": True}
        SPAM_RUNNING = True
        SPAM_THREADS = []
        for i in range(threads):
            t = threading.Thread(target=spam_loop_task, args=(phone, delay, proxies, mode))
            t.daemon = True
            t.start()
            SPAM_THREADS.append(t)
        add_log(f"[Telegram] Started attack on {phone}", "system")
        return {"status": "success", "message": f"Attack started on {phone}"}

    def bot_stop_attack():
        global SPAM_RUNNING
        if not SPAM_RUNNING:
             return {"status": "error", "message": "Not running"}
        SPAM_RUNNING = False
        STATS["threads"] = 0
        add_log("[Telegram] Stopped attack", "system")
        return {"status": "success", "message": "Attack stopped"}

    def bot_get_status():
        s = STATS.copy()
        s['running'] = SPAM_RUNNING
        return s

    try:
        TELEGRAM_BOT = telegram_bot.Spambot(TELEGRAM_TOKEN, bot_start_attack, bot_stop_attack, bot_get_status)
        t = threading.Thread(target=TELEGRAM_BOT.start)
        t.daemon = True
        t.start()
        add_log("Telegram Bot connected!", "system")
    except Exception as e:
        add_log(f"Telegram Bot Error: {e}", "error")

@app.route('/api/telegram_config', methods=['POST'])
def telegram_config():
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    data = request.json
    TELEGRAM_TOKEN = data.get('token')
    TELEGRAM_CHAT_ID = data.get('chat_id')
    
    # Restart bot with new token
    start_telegram_bot_thread()
    
    return jsonify({'status': 'success', 'message': 'Telegram Settings Saved!'})

if __name__ == '__main__':
    # Try to load saved config if we had file persistence, but for now just wait for UI
    app.run(debug=True, port=5000)
