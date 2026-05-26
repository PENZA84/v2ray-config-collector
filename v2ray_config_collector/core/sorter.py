import os
import re
import socket
import requests
import shutil
import concurrent.futures
from urllib.parse import urlparse

class CountrySorter:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(os.path.dirname(self.script_dir))
        self.input_dir = os.path.join(self.root_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.root_dir, 'countries')
        self.protocols = ['vless', 'trojan', 'vmess', 'ss', 'socks5', 'socks4', 'socks', 'http', 'https', 'tuic', 'hysteria', 'hysteria2', 'hy2', 'ssh']
        self.timeout = 3

    def is_trash(self, link):
        link = link.strip()
        return len(link) < 15 or ('://!' in link and (link.endswith('!') or link.endswith('!#')))

    def extract_host(self, link):
        try:
            clean_link = link.split('#')[0]
            parsed = urlparse(clean_link)
            host = parsed.hostname or (clean_link.split('@')[-1].split(':')[0].split('/')[0].split('?')[0])
            return host.strip('!@:/\\ ') if host and ('.' in host or re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host)) else None
        except: return None

    def get_country_code(self, host):
        try:
            ip = socket.gethostbyname(host) if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host) else host
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=self.timeout).json()
            return res.get('countryCode', 'unknown').lower() if res.get('status') == 'success' else 'unknown'
        except: return 'unknown'

    def process_link(self, link):
        if self.is_trash(link): return None
        host = self.extract_host(link)
        if not host: return None
        return {'link': link, 'country': self.get_country_code(host), 'protocol': next((p for p in self.protocols if link.lower().startswith(f"{p}://")), 'unknown')}

    def sort_now(self):
        print(f"[ТАМОЖНЯ] Путь к данным: {self.input_dir}")
        if not os.path.exists(self.input_dir):
            print("[ОШИБКА] Склад уникальных данных пуст!"); return
        
        all_links = set()
        for f_name in os.listdir(self.input_dir):
            if f_name.endswith('.txt'):
                with open(os.path.join(self.input_dir, f_name), 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if '://' in line: all_links.add(line.strip())
        
        print(f"[ТАМОЖНЯ] Обрабатываю {len(all_links)} строк...")
        warehouse = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            for res in executor.map(self.process_link, all_links):
                if res:
                    c, p, l = res['country'], res['protocol'], res['link']
                    warehouse.setdefault(c, {proto: [] for proto in self.protocols + ['unknown']})[p].append(l)

        if os.path.exists(self.output_dir): shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        for country, protos in warehouse.items():
            c_path = os.path.join(self.output_dir, country)
            os.makedirs(c_path, exist_ok=True)
            all_c = []
            for proto, links in protos.items():
                if links:
                    all_c.extend(sorted(links))
                    with open(os.path.join(c_path, f"{proto}.txt"), 'w', encoding='utf-8') as f:
                        f.write("\n".join(sorted(links)))
            with open(os.path.join(c_path, "all.txt"), 'w', encoding='utf-8') as f:
                f.write("\n".join(sorted(all_c)))
        print("[ТАМОЖНЯ] Работа завершена. Склады готовы.")

if __name__ == "__main__":
    CountrySorter().sort_now()
