import requests
import random
import re
import threading

class ProxyScraper:
    def __init__(self):
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
            "https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt",
            "https://raw.githubusercontent.com/roosterkid/openproxylist/master/HTTPS_RAW.txt",
            "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt"
        ]
        self.proxies = []

    def validate_proxies(self, proxies):
        print(f"[System] Checking {len(proxies)} proxies... (This may take a while)")
        valid_proxies = []
        
        def check(proxy):
            try:
                # Test connection to a fast, reliable server
                # Using a low timeout to filter out slow proxies
                r = requests.get("http://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=3)
                if r.status_code == 200:
                    valid_proxies.append(proxy)
            except:
                pass

        # Multithreading for faster validation
        threads = []
        for p in proxies:
            t = threading.Thread(target=check, args=(p,))
            threads.append(t)
            t.start()
            # Limit concurrent threads to avoid system choke
            if len(threads) >= 50:
                 for th in threads: th.join()
                 threads = []
        
        for th in threads: th.join()
        
        print(f"[System] Filtered {len(valid_proxies)} LIVE proxies.")
        return valid_proxies

    def get_proxies(self):
        print("[System] Scanning free proxies from database...")
        collected = set()
        
        for url in self.sources:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    # Regex to find IP:PORT users often list them simply
                    found = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+", response.text)
                    for p in found:
                        collected.add(p)
                    print(f"   + Downloaded {len(found)} proxies from source.")
            except Exception as e:
                print(f"   ! Source Error {url}: {e}")

        all_proxies = list(collected)
        # Validate before returning
        self.proxies = self.validate_proxies(all_proxies)
        
        if not self.proxies:
             print("[System] Warning: No live proxies found. Using unfiltered list.")
             self.proxies = all_proxies # Fallback if validation kills all (rare)

        random.shuffle(self.proxies)
        print(f"[System] Total: {len(self.proxies)} Live Proxies ready for combat!")
        return self.proxies

if __name__ == "__main__":
    scraper = ProxyScraper()
    proxies = scraper.get_proxies()
    print(f"Sample: {proxies[:5]}")
