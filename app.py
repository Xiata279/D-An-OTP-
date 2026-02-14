from flask import Flask, render_template, request, jsonify, Response
import threading
import time
import spam_otp  # Import module spam_otp.py
from datetime import datetime

app = Flask(__name__)

# Global variables
SPAM_RUNNING = False
SPAM_THREAD = None
LOG_MESSAGES = []  # List to store recent logs
MAX_LOGS = 50     # Keep only last 50 logs
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

def spam_loop_task(phone, delay):
    global SPAM_RUNNING, STATS
    spam_instance = spam_otp.SpamOTP(phone)
    
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
    
    STATS["threads"] = 1 # Mark as active
    
    while SPAM_RUNNING:
        try:
            spam_instance.run_batch(delay=delay)
            time.sleep(delay)
        except Exception as e:
            add_log(f"Critical Loop Error: {e}", "error")
            break
            
    STATS["threads"] = 0 # Mark as inactive

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

@app.route('/api/start', methods=['POST'])
def start_spam():
    global SPAM_RUNNING, SPAM_THREAD, STATS, LOG_MESSAGES
    data = request.json
    phone = data.get('phone')
    delay = float(data.get('delay', 2.0))
    
    if not phone or len(phone) < 10:
        return jsonify({'status': 'error', 'message': 'Số điện thoại không hợp lệ'}), 400

    if SPAM_RUNNING:
        return jsonify({'status': 'error', 'message': 'Đang chạy spam rồi!'}), 400

    # Reset stats on new run
    STATS = {"sent": 0, "success": 0, "fail": 0, "threads": 0}
    # LOG_MESSAGES = [] # Optional: Clear logs on start

    SPAM_RUNNING = True
    SPAM_THREAD = threading.Thread(target=spam_loop_task, args=(phone, delay))
    SPAM_THREAD.daemon = True
    SPAM_THREAD.start()
    
    add_log(f"Started attack on {phone} with delay {delay}s", "system")
    return jsonify({'status': 'success', 'message': f'Đã bắt đầu spam sđt: {phone}'})

@app.route('/api/stop', methods=['POST'])
def stop_spam():
    global SPAM_RUNNING
    if not SPAM_RUNNING:
        return jsonify({'status': 'error', 'message': 'Không có tiến trình nào đang chạy'}), 400
    
    SPAM_RUNNING = False
    add_log("Stopping attack...", "system")
    return jsonify({'status': 'success', 'message': 'Đã dừng spam!'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
