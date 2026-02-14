let isRunning = false;
let logInterval = null;

// Sound Effects Removed by User Request
function playBeep() {
    // Disabled
}

// AI Voice Removed by User Request
function speak(text) {
    // Disabled
}

// Visualizer Loop
function startVisualizer() {
    const bars = document.querySelectorAll('.vis-bar');
    setInterval(() => {
        if (isRunning) {
            bars.forEach(bar => {
                const height = Math.random() * 25 + 5;
                if (Math.random() > 0.5) bar.classList.add('active');
                else bar.classList.remove('active');
                bar.style.height = `${height}px`;
            });
        }
    }, 100);
}
startVisualizer();

// Global Hotkeys
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return; // Ignore if typing

    switch (e.key.toLowerCase()) {
        case ' ':
            e.preventDefault();
            if (isRunning) stopSpam();
            else startSpam();
            break;
        case 'g':
            activateGhostMode();
            break;
    }
});

// Update slider value
const delaySlider = document.getElementById('delaySlider');
const delayValue = document.getElementById('delayValue');
const threadSlider = document.getElementById('threadSlider');
const threadValue = document.getElementById('threadValue');

delaySlider.addEventListener('input', (e) => {
    delayValue.textContent = `${parseFloat(e.target.value).toFixed(1)}s`;
    // playBeep(800, 'triangle', 0.05); // SFX Removed
});

threadSlider.addEventListener('input', (e) => {
    threadValue.textContent = e.target.value;
});

// Carrier Detection
function detectCarrier(phone) {
    const badge = document.getElementById('carrierBadge');
    if (phone.length < 3) {
        badge.textContent = 'NET';
        badge.className = 'carrier-badge';
        return;
    }

    const p = phone.substring(0, 3);
    let carrier = 'UNKNOWN';
    let cls = '';

    if (['086', '096', '097', '098', '032', '033', '034', '035', '036', '037', '038', '039'].includes(p)) {
        carrier = 'VIETTEL'; cls = 'viettel';
    } else if (['089', '090', '093', '070', '079', '077', '076', '078'].includes(p)) {
        carrier = 'MOBI'; cls = 'mobi';
    } else if (['088', '091', '094', '083', '084', '085', '081', '082'].includes(p)) {
        carrier = 'VINA'; cls = 'vina';
    } else if (['092', '056', '058'].includes(p)) {
        carrier = 'VNMOBILE'; cls = 'vietnamobile';
    }

    badge.textContent = carrier;
    badge.className = `carrier-badge ${cls}`;
}


// Helper: Append log
function appendLog(message, type = 'system') {
    const consoleBody = document.getElementById('logConsole');
    const div = document.createElement('div');
    div.className = `log-line ${type}`;
    div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    consoleBody.appendChild(div);
    consoleBody.scrollTop = consoleBody.scrollHeight;
}

// Start Spam
async function startSpam() {
    if (isRunning) return;

    const phone = document.getElementById('phoneInput').value;
    const delay = document.getElementById('delaySlider').value;
    const threads = document.getElementById('threadSlider').value;
    const mode = document.getElementById('attackMode').value;
    const auto_proxy = document.getElementById('autoProxy').checked;

    // Retrieve proxies from LocalStorage for persistence across pages
    const proxies = localStorage.getItem('spam_proxies') || '';

    if (!phone || phone.length < 9) {
        appendLog('LỖI: SỐ ĐIỆN THOẠI KHÔNG HỢP LỆ', 'error');
        playBeep(200, 'sawtooth', 0.3); // Error sound
        speak("Báo lỗi. Số điện thoại, không hợp lệ.");
        return;
    }

    // Toggle Buttons
    document.getElementById('btnStart').disabled = true;
    document.getElementById('btnStop').disabled = false;
    isRunning = true;

    playBeep(1000, 'sine', 0.1); // Start beep
    speak("Hệ thống, đã sẵn sàng. Bắt đầu tấn công.");

    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, delay, threads, proxies, mode, auto_proxy })
        });
        const data = await response.json();

        if (data.status === 'success') {
            appendLog(`ĐÃ KHÓA MỤC TIÊU: ${phone}`, 'success');
            appendLog(`CẤU HÌNH: ${threads} LUỒNG | ĐỘ TRỄ ${delay}s`, 'info');
            if (proxies.trim()) appendLog(`PROXY: ĐÃ BẬT (${proxies.split('\n').length} IPs)`, 'info');

            // Start polling real logs
            startRealPolling();
        } else {
            appendLog(`LỖI KHỞI TẠO: ${data.message}`, 'error');
            document.getElementById('btnStart').disabled = false;
            document.getElementById('btnStop').disabled = true;
            isRunning = false;
        }
    } catch (error) {
        console.error('Error:', error);
        appendLog('KẾT NỐI THẤT BẠI', 'error');
        document.getElementById('btnStart').disabled = false;
        document.getElementById('btnStop').disabled = true;
        isRunning = false;
    }
}

// Stop Spam
async function stopSpam() {
    if (!isRunning) return;

    isRunning = false;

    playBeep(400, 'square', 0.2); // Stop sound
    speak("Đang dừng, toàn bộ tiến trình.");

    // Toggle Buttons
    document.getElementById('btnStart').disabled = false;
    document.getElementById('btnStop').disabled = true;

    try {
        await fetch('/api/stop', { method: 'POST' });
        appendLog('ĐÃ DỪNG TẤN CÔNG', 'warning');
        stopRealPolling();
    } catch (error) {
        console.error('Error:', error);
    }
}

// Ghost Mode
async function activateGhostMode() {
    const btnGhost = document.getElementById('btnGhost');

    if (btnGhost.disabled) return;

    const originalText = btnGhost.innerHTML;

    btnGhost.disabled = true;
    btnGhost.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> ĐANG ẨN DANH...';

    playBeep(1200, 'sine', 0.5); // Ghost sound
    speak("Chế độ ẩn danh, đã kích hoạt. Đang xóa dấu vết.");

    try {
        const response = await fetch('/api/reset_identity', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            appendLog('ĐÃ ĐỔI NHẬN DẠNG: USER-AGENT MỚI', 'success');
            document.getElementById('proxyStatus').textContent = 'Trạng thái: An toàn';
            setTimeout(() => document.getElementById('proxyStatus').textContent = 'Trạng thái: Bị lộ', 2000);
        } else {
            appendLog('ĐỔI NHẬN DẠNG THẤT BẠI', 'error');
        }
    } catch (error) {
        appendLog('LỖI CHẾ ĐỘ ẨN DANH', 'error');
    } finally {
        setTimeout(() => {
            btnGhost.disabled = false;
            btnGhost.innerHTML = originalText;
        }, 1500);
    }
}

// Poll for real status
async function pollStatus() {
    if (!isRunning) return;

    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        // Update stats
        if (data.stats) {
            document.getElementById('statsSent').textContent = data.stats.sent;
            document.getElementById('statsSuccess').textContent = data.stats.success;
            document.getElementById('statsFail').textContent = data.stats.fail;
        }

        // Update logs
        if (data.logs && data.logs.length > 0) {
            const consoleBody = document.getElementById('logConsole');
            consoleBody.innerHTML = '';

            data.logs.forEach(log => {
                const div = document.createElement('div');
                div.className = `log-line ${log.type}`;
                div.textContent = log.text;
                consoleBody.appendChild(div);

                // Beep on success/fail
                if (log.type === 'error') playBeep(200, 'sawtooth', 0.1);
            });
            consoleBody.scrollTop = consoleBody.scrollHeight;
        }

        if (!data.running && isRunning) {
            isRunning = false;
            document.getElementById('btnStart').disabled = false;
            document.getElementById('btnStop').disabled = true;
            appendLog("ĐỒNG BỘ: MÁY CHỦ ĐÃ DỪNG", 'warning');
            stopRealPolling();
            speak("Máy chủ, đã ngắt kết nối.");
        }

    } catch (error) {
        console.error("Polling error:", error);
    }
}

function startRealPolling() {
    document.getElementById('logConsole').innerHTML = '';
    logInterval = setInterval(pollStatus, 1000);
}

function stopRealPolling() {
    if (logInterval) clearInterval(logInterval);
}

document.addEventListener('DOMContentLoaded', () => {
    // Check local storage for proxies count
    const savedProxies = localStorage.getItem('spam_proxies') || '';
    const count = savedProxies.split('\n').filter(l => l.trim() !== '').length;
    const statusBadge = document.getElementById('proxyStatus');
    if (statusBadge) statusBadge.innerText = count;

    // Restore delay value
    const savedDelay = localStorage.getItem('spam_delay');
});
