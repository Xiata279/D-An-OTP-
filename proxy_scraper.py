import requests
import random
import re

class ProxyScraper:
    def __init__(self):
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        ]
        self.proxies = []

    def get_proxies(self):
        print("[System] Đang quét Proxy miễn phí từ kho dữ liệu...")
        collected = set()
        
        for url in self.sources:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    # Regex to find IP:PORT users often list them simply
                    found = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+", response.text)
                    for p in found:
                        collected.add(p)
                    print(f"   + Đã tải {len(found)} proxy từ nguồn.")
            except Exception as e:
                print(f"   ! Lỗi nguồn {url}: {e}")

        self.proxies = list(collected)
        random.shuffle(self.proxies)
        print(f"[System] Tổng cộng: {len(self.proxies)} Live Proxies sẵn sàng chiến đấu!")
        return self.proxies

if __name__ == "__main__":
    scraper = ProxyScraper()
    proxies = scraper.get_proxies()
    print(f"Sample: {proxies[:5]}")
