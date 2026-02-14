let isRunning = false;
let logInterval = null;

// Sound Effects
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playBeep(freq = 600, type = 'sine', duration = 0.1) {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    gain.gain.exponentialRampToValueAtTime(0.00001, audioCtx.currentTime + duration);
    osc.stop(audioCtx.currentTime + duration);
}

// AI Voice
function speak(text) {
    if ('speechSynthesis' in window) {
        // Cancel current speech to avoid queue buildup
        speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.pitch = 1.0;
        utterance.rate = 0.9; // Slightly slower for clearer Vietnamese tones

        // Wait for voices to load (Chrome issue)
        let voices = speechSynthesis.getVoices();

        // Retry getting voices if empty
        if (voices.length === 0) {
            speechSynthesis.onvoiceschanged = () => speak(text);
            return;
        }

        // Priority List: Female Vietnamese Voices
        // 1. Google tiếng Việt (Female by default)
        // 2. Microsoft HoaiMy (Female)
        // 3. Apple Linh (Female)
        // 4. Any Vietnamese voice marked as "Female"

        const viVoice = voices.find(v => v.name.includes('Google tiếng Việt')) ||
            voices.find(v => v.name.includes('HoaiMy')) ||
            voices.find(v => v.name.includes('Linh')) ||
            voices.find(v => v.lang === 'vi-VN' && v.name.includes('Female')) ||
            voices.find(v => v.lang === 'vi-VN'); // Fallback

        if (viVoice) {
            utterance.voice = viVoice;
            utterance.lang = 'vi-VN';
        }

        speechSynthesis.speak(utterance);
    }
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

delaySlider.addEventListener('input', (e) => {
    delayValue.textContent = `${parseFloat(e.target.value).toFixed(1)}s`;
    playBeep(800, 'triangle', 0.05); // Tick sound
});

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

    if (!phone || phone.length < 9) {
        appendLog('ERROR: INVALID TARGET NUMBER', 'error');
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
            body: JSON.stringify({ phone, delay })
        });
        const data = await response.json();

        if (data.status === 'success') {
            appendLog(`TARGET LOCKED: ${phone}`, 'success');
            appendLog(`INJECTION DELAY: ${delay}s`, 'info');

            // Start polling real logs
            startRealPolling();
        } else {
            appendLog(`INIT ERROR: ${data.message}`, 'error');
            document.getElementById('btnStart').disabled = false;
            document.getElementById('btnStop').disabled = true;
            isRunning = false;
        }
    } catch (error) {
        console.error('Error:', error);
        appendLog('CONNECTION FAILED', 'error');
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
        appendLog('ATTACK TERMINATED BY USER', 'warning');
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
    btnGhost.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> MASKING IDENTITY...';

    playBeep(1200, 'sine', 0.5); // Ghost sound
    speak("Chế độ ẩn danh, đã kích hoạt. Đang xóa dấu vết.");

    try {
        const response = await fetch('/api/reset_identity', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            appendLog('IDENTITY RESET: NEW SESSION & UA GENERATED', 'success');
            document.getElementById('proxyStatus').textContent = 'Identity: Secure';
            setTimeout(() => document.getElementById('proxyStatus').textContent = 'Identity: Exposed', 2000);
        } else {
            appendLog('IDENTITY RESET FAILED', 'error');
        }
    } catch (error) {
        appendLog('GHOST MODE ERROR', 'error');
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
            appendLog("SYNC: SERVER HALTED ATTACK", 'warning');
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
