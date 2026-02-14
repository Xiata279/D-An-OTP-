let isRunning = false;
let logInterval = null;

// Slider logic
const delaySlider = document.getElementById('delaySlider');
const delayValue = document.getElementById('delayValue');

delaySlider.addEventListener('input', function () {
    delayValue.textContent = this.value + 's';
});

function appendLog(message, type = 'system') {
    const consoleBody = document.getElementById('logConsole');
    const div = document.createElement('div');
    div.className = `log-line ${type}`;
    // Add timestamp similar to VS Code output?
    const time = new Date().toLocaleTimeString();
    div.textContent = `[${time}] ${message}`;
    consoleBody.appendChild(div);
    consoleBody.scrollTop = consoleBody.scrollHeight;
}

async function startSpam() {
    const phone = document.getElementById('phoneInput').value;
    const delay = document.getElementById('delaySlider').value;

    if (phone.length < 10) {
        appendLog("Error: Invalid phone number format.", "error");
        return;
    }

    if (isRunning) return;

    try {
        appendLog(`Debugger attached. Launching Process ID: ${Math.floor(Math.random() * 10000)}...`, 'info');

        const response = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: phone, delay: delay })
        });
        const data = await response.json();

        if (data.status === 'success') {
            isRunning = true;
            document.getElementById('btnStart').disabled = true;
            document.getElementById('btnStop').disabled = false;

            appendLog(`Target: ${phone} | Delay: ${delay}s`, 'success');
            appendLog('Thread pool initialized. Starting requests...', 'system');

            // Start polling real logs
            startRealPolling();
        } else {
            appendLog(`Error: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        appendLog('Fatal Error: Connection refused.', 'error');
    }
}

async function stopSpam() {
    if (!isRunning) return;

    try {
        const response = await fetch('/api/stop', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            isRunning = false;
            document.getElementById('btnStart').disabled = false;
            document.getElementById('btnStop').disabled = true;

            appendLog('Process terminated by user.', 'warning');
            stopRealPolling();
        }
    } catch (error) {
        console.error('Error:', error);
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
            document.getElementById('statsSuccess').textContent = data.stats.success; // You might want a rate calculation here
            document.getElementById('statsThreads').textContent = data.stats.threads;
        }

        // Update logs
        if (data.logs && data.logs.length > 0) {
            const consoleBody = document.getElementById('logConsole');
            consoleBody.innerHTML = ''; // Clear current logs (or append smartly)
            // Ideally we should append only new ones, but for simplicity let's just render the list
            // actually clearing every time might be flickering. 
            // Let's just append the last few if we can track them, or just dump them all since list is capped at 50.

            data.logs.forEach(log => {
                const div = document.createElement('div');
                div.className = `log-line ${log.type}`;
                div.textContent = log.text;
                consoleBody.appendChild(div);
            });
            consoleBody.scrollTop = consoleBody.scrollHeight;
        }

        if (!data.running && isRunning) {
            // Server stopped but client thinks running?
            // Sync state
            isRunning = false;
            document.getElementById('btnStart').disabled = false;
            document.getElementById('btnStop').disabled = true;
            appendLog("Sync: Process stopped on server.", "warning");
        }

    } catch (error) {
        console.error("Polling error:", error);
    }
}

function startRealPolling() {
    // Clear logs to start fresh
    document.getElementById('logConsole').innerHTML = '';
    logInterval = setInterval(pollStatus, 1000); // Poll every 1s
}

function stopRealPolling() {
    if (logInterval) clearInterval(logInterval);
}
