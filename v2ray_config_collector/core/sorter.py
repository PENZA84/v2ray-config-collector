import os
import re
import socket
import requests
import shutil
import concurrent.futures
from urllib.parse import urlparse

class CountrySorter:
    def __init__(self):
        # Пути настроены так, чтобы всё работало точно по твоей структуре
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_dir = os.path.join(os.path.dirname(os.path.dirname(self.base_dir)), 'data', 'unique')
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(self.base_dir)), 'countries')
        
        self.protocols = [
            'vless', 'trojan', 'vmess', 'ss', 'socks5', 'socks4', 'socks', 
            'http', 'https', 'tuic', 'hysteria', 'hysteria2', 'hy2', 'ssh'
        ]
        self.timeout = 3

    def is_trash(self, link):
        link = link.strip()
        if len(link) < 15 or '://!' in link and (link.endswith('!') or link.endswith('!#')):
            return True
        return False

    def extract_host(self, link):
        try:
            clean_link = link.split('#')[0]
            parsed = urlparse(clean_link)
            host = parsed.hostname
            if not host or '@' in parsed.netloc:
                remain = clean_link.split('@')[-1] if '@' in clean_link else clean_link.split('://')[-1]
                host = remain.split(':')[0].split('/')[0].split('?')[0]
            if host:
                host = host.strip('!@:/\\ ')
            if host and ('.' in host or re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host)):
                return host
        except Exception:
            pass
        return None

    def get_country_code(self, host):
        if not host: return "unknown"
        try:
            ip = socket.gethostbyname(host) if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host) else host
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=self.timeout).json()
            if res.get('status') == 'success': return res.get('countryCode').lower()
        except Exception: pass
        return "unknown"

    def process_link(self, link):
        if self.is_trash(link): return None
        host = self.extract_host(link)
        if not host: return None
        country_code = self.get_country_code(host)
        proto_found = next((p for p in self.protocols if link.lower().startswith(f"{p}://")), 'unknown')
        return {'link': link, 'country': country_code, 'protocol': proto_found}

    def sort_now(self):
        if not os.path.exists(self.input_dir): return
        all_links = set()
        for filename in os.listdir(self.input_dir):
            if filename.endswith('.txt') and filename != 'dns_list.txt':
                with open(os.path.join(self.input_dir, filename), 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if '://' in line: all_links.add(line.strip())

        warehouse = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(self.process_link, all_links)
            for res in results:
                if res:
                    c, p, l = res['country'], res['protocol'], res['link']
                    if c not in warehouse: warehouse[c] = {proto: [] for proto in self.protocols + ['unknown']}
                    warehouse[c][p].append(l)

        if os.path.exists(self.output_dir): shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        for country, protos in warehouse.items():
            country_path = os.path.join(self.output_dir, country)
            os.makedirs(country_path, exist_ok=True)
            all_c = []
            for proto, links in protos.items():
                if links:
                    sorted_links = sorted(links)
                    all_c.extend(sorted_links)
                    with open(os.path.join(country_path, f"{proto}.txt"), 'w', encoding='utf-8') as f:
                        f.write("\n".join(sorted_links))
            if all_c:
                with open(os.path.join(country_path, "all.txt"), 'w', encoding='utf-8') as f:
                    f.write("\n".join(sorted(all_c)))

if __name__ == "__main__":
    CountrySorter().sort_now()
