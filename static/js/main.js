let isRunning = false;
let eventSource = null;
let elapsedInterval = null;
let elapsedSeconds = 0;
let matrixInterval = null;
let notificationsEnabled = false;

// === Request Notification Permission ===
async function requestNotifications() {
    if ('Notification' in window) {
        const perm = await Notification.requestPermission();
        notificationsEnabled = (perm === 'granted');
    }
}
requestNotifications();

function sendDesktopNotification(title, body, icon = '🚀') {
    if (!notificationsEnabled) return;
    try {
        new Notification(title, { body, icon, silent: false });
    } catch (e) { /* ignore */ }
}

// === Sound (Disabled) ===
function playBeep() { }
function speak() { }

// === Visualizer ===
function startVisualizer() {
    const bars = document.querySelectorAll('.vis-bar');
    setInterval(() => {
        if (isRunning) {
            bars.forEach(bar => {
                const height = Math.random() * 30 + 5;
                if (Math.random() > 0.4) bar.classList.add('active');
                else bar.classList.remove('active');
                bar.style.height = `${height}px`;
            });
        } else {
            bars.forEach(bar => {
                bar.classList.remove('active');
                bar.style.height = '5px';
            });
        }
    }, 80);
}
startVisualizer();

// === Matrix Rain ===
function startMatrixRain() {
    const canvas = document.getElementById('matrixCanvas');
    if (!canvas) return;
    canvas.style.display = 'block';
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const chars = 'OTPスパムLUÂNEM01アイウエオカ'.split('');
    const fontSize = 12;
    const columns = Math.floor(canvas.width / fontSize);
    const drops = new Array(columns).fill(1);

    function draw() {
        ctx.fillStyle = 'rgba(5, 5, 16, 0.04)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'rgba(0, 255, 157, 0.6)';
        ctx.font = fontSize + 'px monospace';
        for (let i = 0; i < drops.length; i++) {
            const text = chars[Math.floor(Math.random() * chars.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
            drops[i]++;
        }
    }
    matrixInterval = setInterval(draw, 40);
}

function stopMatrixRain() {
    const canvas = document.getElementById('matrixCanvas');
    if (canvas) { canvas.style.display = 'none'; const ctx = canvas.getContext('2d'); ctx.clearRect(0, 0, canvas.width, canvas.height); }
    if (matrixInterval) { clearInterval(matrixInterval); matrixInterval = null; }
}

// === Hotkeys ===
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    switch (e.key.toLowerCase()) {
        case ' ': e.preventDefault(); if (isRunning) stopSpam(); else startSpam(); break;
        case 'g': activateGhostMode(); break;
    }
});

// === Sliders ===
const delaySlider = document.getElementById('delaySlider');
const delayValue = document.getElementById('delayValue');
const threadSlider = document.getElementById('threadSlider');
const threadValue = document.getElementById('threadValue');
delaySlider.addEventListener('input', (e) => { delayValue.textContent = `${parseFloat(e.target.value).toFixed(1)}s`; });
threadSlider.addEventListener('input', (e) => { threadValue.textContent = e.target.value; });

// === Carrier Detection ===
function detectCarrier(phone) {
    const badge = document.getElementById('carrierBadge');
    if (!badge) return;
    if (phone.length < 3) { badge.textContent = 'NET'; badge.className = 'carrier-badge'; return; }
    const p = phone.substring(0, 3);
    let carrier = 'UNKNOWN', cls = '';
    if (['086', '096', '097', '098', '032', '033', '034', '035', '036', '037', '038', '039'].includes(p)) { carrier = 'VIETTEL'; cls = 'viettel'; }
    else if (['089', '090', '093', '070', '079', '077', '076', '078'].includes(p)) { carrier = 'MOBI'; cls = 'mobi'; }
    else if (['088', '091', '094', '083', '084', '085', '081', '082'].includes(p)) { carrier = 'VINA'; cls = 'vina'; }
    else if (['092', '056', '058'].includes(p)) { carrier = 'VNMOBILE'; cls = 'vietnamobile'; }
    badge.textContent = carrier;
    badge.className = `carrier-badge ${cls}`;
}

// === Log Append ===
function appendLog(message, type = 'system') {
    const consoleBody = document.getElementById('logConsole');
    if (!consoleBody) return;
    const div = document.createElement('div');
    div.className = `log-line ${type}`;
    div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    consoleBody.appendChild(div);
    consoleBody.scrollTop = consoleBody.scrollHeight;
    if (type === 'success') spawnParticle();
}

// === Elapsed Timer ===
function startElapsedTimer() {
    elapsedSeconds = 0;
    const el = document.getElementById('elapsedTimer');
    if (el) el.textContent = '00:00';
    elapsedInterval = setInterval(() => {
        elapsedSeconds++;
        const m = String(Math.floor(elapsedSeconds / 60)).padStart(2, '0');
        const s = String(elapsedSeconds % 60).padStart(2, '0');
        if (el) el.textContent = `${m}:${s}`;
    }, 1000);
}
function stopElapsedTimer() { if (elapsedInterval) { clearInterval(elapsedInterval); elapsedInterval = null; } }

// === SSE Streaming ===
function startSSE() {
    if (eventSource) eventSource.close();
    eventSource = new EventSource('/api/stream');

    eventSource.onmessage = function (event) {
        try {
            const data = JSON.parse(event.data);
            if (data.stats) {
                document.getElementById('statsSent').textContent = data.stats.sent;
                document.getElementById('statsSuccess').textContent = data.stats.success;
                document.getElementById('statsFail').textContent = data.stats.fail;
                const rateEl = document.getElementById('successRate');
                if (rateEl && data.stats.sent > 0) {
                    rateEl.textContent = `${Math.round((data.stats.success / data.stats.sent) * 100)}%`;
                }
                // Speed calculation
                const speedEl = document.getElementById('speedRate');
                if (speedEl && elapsedSeconds > 0) {
                    speedEl.textContent = `${Math.round(data.stats.sent / (elapsedSeconds / 60))}/m`;
                }
            }
            if (data.logs && data.logs.length > 0) {
                const consoleBody = document.getElementById('logConsole');
                data.logs.forEach(log => {
                    const div = document.createElement('div');
                    div.className = `log-line ${log.type}`;
                    div.textContent = log.text;
                    consoleBody.appendChild(div);
                    if (log.type === 'success') spawnParticle();
                });
                consoleBody.scrollTop = consoleBody.scrollHeight;
            }
            if (!data.running && isRunning) {
                isRunning = false;
                document.getElementById('btnStart').disabled = false;
                document.getElementById('btnStop').disabled = true;
                stopSSE(); stopElapsedTimer(); stopMatrixRain();
                sendDesktopNotification('🛑 LuânEm Tool', `Đã dừng! Gửi: ${data.stats.sent} | OK: ${data.stats.success}`);
            }
        } catch (e) { console.error("SSE error:", e); }
    };

    eventSource.onerror = function () { stopSSE(); startFallbackPolling(); };
}
function stopSSE() { if (eventSource) { eventSource.close(); eventSource = null; } }

// Fallback
let fallbackInterval = null;
function startFallbackPolling() {
    if (!isRunning) return;
    fallbackInterval = setInterval(async () => {
        if (!isRunning) { clearInterval(fallbackInterval); return; }
        try {
            const resp = await fetch('/api/status');
            const data = await resp.json();
            document.getElementById('statsSent').textContent = data.stats.sent;
            document.getElementById('statsSuccess').textContent = data.stats.success;
            document.getElementById('statsFail').textContent = data.stats.fail;
            const consoleBody = document.getElementById('logConsole');
            consoleBody.innerHTML = '';
            data.logs.forEach(log => {
                const div = document.createElement('div');
                div.className = `log-line ${log.type}`;
                div.textContent = log.text;
                consoleBody.appendChild(div);
            });
            consoleBody.scrollTop = consoleBody.scrollHeight;
            if (!data.running) {
                isRunning = false;
                document.getElementById('btnStart').disabled = false;
                document.getElementById('btnStop').disabled = true;
                clearInterval(fallbackInterval);
                stopElapsedTimer(); stopMatrixRain();
            }
        } catch (e) { }
    }, 1500);
}

// === Particles ===
function spawnParticle() {
    const c = document.querySelector('.bento-container');
    if (!c) return;
    const p = document.createElement('div');
    p.className = 'success-particle';
    p.textContent = ['✓', '⚡', '💥', '🎯'][Math.floor(Math.random() * 4)];
    p.style.left = Math.random() * 80 + 10 + '%';
    p.style.top = Math.random() * 80 + 10 + '%';
    c.appendChild(p);
    setTimeout(() => p.remove(), 1200);
}

// === START ===
async function startSpam() {
    if (isRunning) return;
    const phone = document.getElementById('phoneInput').value;
    const delay = document.getElementById('delaySlider').value;
    const threads = document.getElementById('threadSlider').value;
    const mode = document.getElementById('attackMode')?.value || 'carpet';
    const auto_proxy = document.getElementById('autoProxy').checked;
    const proxies = localStorage.getItem('spam_proxies') || '';

    if (!phone || phone.length < 9) { appendLog('❌ SĐT không hợp lệ', 'error'); return; }

    document.getElementById('btnStart').disabled = true;
    document.getElementById('btnStop').disabled = false;
    isRunning = true;
    document.getElementById('logConsole').innerHTML = '';

    sendDesktopNotification('🚀 LuânEm Tool', `Bắt đầu tấn công ${phone}`);

    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, delay, threads, proxies, mode, auto_proxy })
        });
        const data = await response.json();
        if (data.status === 'success') {
            appendLog(`🎯 ${phone}`, 'success');
            appendLog(`⚡ ${threads} luồng | ${delay}s | ${mode.toUpperCase()} | ASYNC`, 'info');
            startSSE();
            startElapsedTimer();
            startMatrixRain();
        } else {
            appendLog(`❌ ${data.message}`, 'error');
            document.getElementById('btnStart').disabled = false;
            document.getElementById('btnStop').disabled = true;
            isRunning = false;
        }
    } catch (error) {
        appendLog('❌ Lỗi kết nối', 'error');
        document.getElementById('btnStart').disabled = false;
        document.getElementById('btnStop').disabled = true;
        isRunning = false;
    }
}

// === STOP ===
async function stopSpam() {
    if (!isRunning) return;
    isRunning = false;
    document.getElementById('btnStart').disabled = false;
    document.getElementById('btnStop').disabled = true;
    try {
        await fetch('/api/stop', { method: 'POST' });
        appendLog('🛑 ĐÃ DỪNG', 'warning');
        stopSSE(); stopElapsedTimer(); stopMatrixRain();
        const sent = document.getElementById('statsSent').textContent;
        const ok = document.getElementById('statsSuccess').textContent;
        sendDesktopNotification('🛑 Đã dừng', `Gửi: ${sent} | OK: ${ok}`);
    } catch (e) { }
}

// === Ghost Mode ===
async function activateGhostMode() {
    const btn = document.getElementById('btnGhost');
    if (!btn || btn.disabled) return;
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    try {
        const resp = await fetch('/api/reset_identity', { method: 'POST' });
        const data = await resp.json();
        appendLog(data.status === 'success' ? '🔄 Identity rotated' : '❌ Thất bại', data.status === 'success' ? 'success' : 'error');
    } catch (e) { appendLog('❌ Error', 'error'); }
    finally { setTimeout(() => { btn.disabled = false; btn.innerHTML = orig; }, 1000); }
}

// === Theme Toggle ===
let isDarkMode = true;
function toggleTheme() {
    isDarkMode = !isDarkMode;
    const r = document.documentElement;
    if (!isDarkMode) {
        r.style.setProperty('--bg-deep', '#f0f2f5');
        r.style.setProperty('--glass-bg', 'rgba(255,255,255,0.7)');
        r.style.setProperty('--text-primary', '#1a1a2e');
        r.style.setProperty('--text-secondary', 'rgba(0,0,0,0.6)');
        r.style.setProperty('--glass-border', 'rgba(0,0,0,0.08)');
    } else {
        r.style.setProperty('--bg-deep', '#050510');
        r.style.setProperty('--glass-bg', 'rgba(20,20,35,0.4)');
        r.style.setProperty('--text-primary', '#ffffff');
        r.style.setProperty('--text-secondary', 'rgba(255,255,255,0.7)');
        r.style.setProperty('--glass-border', 'rgba(255,255,255,0.08)');
    }
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    const btn = document.getElementById('themeToggle');
    if (btn) btn.innerHTML = isDarkMode ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
}

// === DOMContentLoaded ===
document.addEventListener('DOMContentLoaded', () => {
    const savedProxies = localStorage.getItem('spam_proxies') || '';
    const count = savedProxies.split('\n').filter(l => l.trim()).length;
    const badge = document.getElementById('proxyStatus');
    if (badge) badge.innerText = count;

    const savedDelay = localStorage.getItem('spam_delay');
    if (savedDelay) {
        document.getElementById('delaySlider').value = savedDelay;
        document.getElementById('delayValue').textContent = `${parseFloat(savedDelay).toFixed(1)}s`;
    }

    if (localStorage.getItem('theme') === 'light') { isDarkMode = true; toggleTheme(); }
});

// === Telegram Modal ===
function openTelegramModal() {
    document.getElementById('telegramModal').style.display = "block";
    document.getElementById('teleToken').value = localStorage.getItem('tele_token') || '';
    document.getElementById('teleChatId').value = localStorage.getItem('tele_chat_id') || '';
}
function closeTelegramModal() { document.getElementById('telegramModal').style.display = "none"; }
window.onclick = function (event) {
    const modal = document.getElementById('telegramModal');
    if (event.target == modal) modal.style.display = "none";
}
async function saveTelegramConfig() {
    const token = document.getElementById('teleToken').value;
    const chatId = document.getElementById('teleChatId').value;
    if (!token) { alert("Nhập Token!"); return; }
    localStorage.setItem('tele_token', token);
    localStorage.setItem('tele_chat_id', chatId);
    try {
        const resp = await fetch('/api/telegram_config', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, chat_id: chatId })
        });
        const data = await resp.json();
        appendLog(data.status === 'success' ? '✅ Telegram saved' : '❌ Lỗi', data.status === 'success' ? 'success' : 'error');
        if (data.status === 'success') closeTelegramModal();
    } catch (e) { appendLog('❌ Lỗi kết nối', 'error'); }
}

// === AI Stats Modal ===
async function showAIStats() {
    try {
        const resp = await fetch('/api/ai_stats');
        const data = await resp.json();
        const modal = document.getElementById('aiModal');
        const body = document.getElementById('aiStatsBody');
        if (!modal || !body) return;

        const sorted = Object.entries(data).sort((a, b) => b[1].score - a[1].score);
        body.innerHTML = sorted.map(([name, info]) => {
            const bar = `<div class="ai-bar" style="width:${info.score}%;background:${info.score > 60 ? 'var(--neon-green)' : info.score > 30 ? 'var(--warning)' : 'var(--danger)'}"></div>`;
            return `<div class="ai-row"><span class="ai-name">${name}</span><div class="ai-bar-bg">${bar}</div><span class="ai-score">${info.score}</span>${info.cooldown ? '<span class="ai-cd">⏸</span>' : ''}</div>`;
        }).join('');

        modal.style.display = 'block';
    } catch (e) { appendLog('❌ No AI data', 'error'); }
}
function closeAIModal() { document.getElementById('aiModal').style.display = 'none'; }
