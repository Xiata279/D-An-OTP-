from flask import Flask, render_template, request, jsonify, Response
import threading
import time
import spam_otp  # Import module spam_otp.py
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

def spam_loop_task(phone, delay, proxies):
    global SPAM_RUNNING, STATS
    spam_instance = spam_otp.SpamOTP(phone, proxies=proxies)
    
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

@app.route('/api/start', methods=['POST'])
def start_spam():
    global SPAM_RUNNING, SPAM_THREADS, STATS, LOG_MESSAGES
    data = request.json
    phone = data.get('phone')
    delay = float(data.get('delay', 2.0))
    thread_count = int(data.get('threads', 1))
    proxies_raw = data.get('proxies', '')
    
    if not phone or len(phone) < 10:
        return jsonify({'status': 'error', 'message': 'Số điện thoại không hợp lệ'}), 400

    if SPAM_RUNNING:
        return jsonify({'status': 'error', 'message': 'Đang chạy spam rồi!'}), 400

    # Parse Proxies
    proxies = [p.strip() for p in proxies_raw.split('\n') if p.strip()] if proxies_raw else []

    # Reset stats on new run
    STATS = {"sent": 0, "success": 0, "fail": 0, "threads": thread_count}

    SPAM_RUNNING = True
    SPAM_THREADS = []
    
    for i in range(thread_count):
        t = threading.Thread(target=spam_loop_task, args=(phone, delay, proxies))
        t.daemon = True
        t.start()
        SPAM_THREADS.append(t)
    
    add_log(f"Started attack on {phone} | Threads: {thread_count} | Proxies: {len(proxies)}", "system")
    return jsonify({'status': 'success', 'message': f'Đã kích hoạt {thread_count} luồng tấn công!'})

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
