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
let selectedVoice = null;
const GOOGLE_VI_VOICE_NAME = "Google Online (Nữ/Chuẩn)";

function populateVoiceList() {
    const voiceSelect = document.getElementById('voiceSelect');
    voiceSelect.innerHTML = '';

    // 1. ADD GOOGLE ONLINE OPTION (Priority #1)
    const googleOption = document.createElement('option');
    googleOption.textContent = `🌐 ${GOOGLE_VI_VOICE_NAME}`;
    googleOption.value = 'google_online';
    googleOption.selected = true; // Auto-select this as it's the best
    voiceSelect.appendChild(googleOption);

    // Set default
    selectedVoice = 'google_online';

    // 2. Add Local Voices
    if (typeof speechSynthesis !== 'undefined') {
        let voices = speechSynthesis.getVoices();

        // Retry logic for Chrome
        if (voices.length === 0) {
            speechSynthesis.onvoiceschanged = () => {
                // Don't wipe the Google option, just append locals
                const freshVoices = speechSynthesis.getVoices();
                addLocalVoices(freshVoices, voiceSelect);
            };
        } else {
            addLocalVoices(voices, voiceSelect);
        }
    }
}

function addLocalVoices(voices, selectElement) {
    // Filter for meaningful voices AND remove duplicates
    const relevantVoices = voices.filter(v => v.lang.includes('vi') || v.lang.includes('en'));

    relevantVoices.forEach((voice) => {
        // Skip if it looks like a duplicate
        if (selectElement.querySelector(`option[value="${voice.name}"]`)) return;

        const option = document.createElement('option');
        option.textContent = `💻 ${voice.name} (${voice.lang})`;
        option.value = voice.name;
        selectElement.appendChild(option);
    });
}

// Event Listener for Voice Change
document.getElementById('voiceSelect').addEventListener('change', (e) => {
    if (e.target.value === 'google_online') {
        selectedVoice = 'google_online';
    } else {
        const voices = speechSynthesis.getVoices();
        selectedVoice = voices.find(v => v.name === e.target.value);
    }
    speak("Đã chọn giọng nói này.");
});

// Initialize Voices
populateVoiceList();

function speak(text) {
    // Clean text for URL (remove special chars if needed, but encodeURIComponent handles it)

    // CASE 1: Google Online Voice
    if (selectedVoice === 'google_online') {
        try {
            const url = `https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=vi&q=${encodeURIComponent(text)}`;
            const audio = new Audio(url);
            audio.play().catch(e => console.error("Audio Play Error:", e));
        } catch (e) {
            console.error("Google TTS Error:", e);
            // Fallback to local
            speakLocal(text);
        }
        return;
    }

    // CASE 2: Local Voice
    speakLocal(text);
}

function speakLocal(text) {
    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.pitch = 1.0;
        utterance.rate = 0.9;

        if (selectedVoice && typeof selectedVoice !== 'string') {
            utterance.voice = selectedVoice;
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
