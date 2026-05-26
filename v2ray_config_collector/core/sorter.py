import os
import re
import json
import asyncio
import aiohttp
import shutil
import concurrent.futures
from urllib.parse import urlparse

class CountrySorter:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(os.path.dirname(self.script_dir))
        self.input_dir = os.path.join(self.root_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.root_dir, 'countries')
        self.cache_file = os.path.join(self.root_dir, 'ip_cache.json')
        self.cache = self.load_cache()
        self.protocols = ['vless', 'trojan', 'vmess', 'ss', 'socks5', 'socks4', 'socks', 'http', 'https', 'tuic', 'hysteria', 'hysteria2', 'hy2', 'ssh']

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f: return json.load(f)
        return {}

    def save_cache(self):
        with open(self.cache_file, 'w') as f: json.dump(self.cache, f)

    def extract_host(self, link):
        try:
            clean_link = link.split('#')[0]
            host = urlparse(clean_link).hostname or clean_link.split('@')[-1].split(':')[0].split('/')[0].split('?')[0]
            return host.strip('!@:/\\ ') if host and ('.' in host or re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host)) else None
        except: return None

    async def get_country(self, session, host):
        if host in self.cache: return self.cache[host]
        try:
            async with session.get(f"http://ip-api.com/json/{host}?fields=status,countryCode", timeout=2) as resp:
                data = await resp.json()
                code = data.get('countryCode', 'unknown').lower() if data.get('status') == 'success' else 'unknown'
                self.cache[host] = code
                return code
        except: return 'unknown'

    async def process_link(self, session, link):
        host = self.extract_host(link)
        if not host: return None
        country = await self.get_country(session, host)
        proto = next((p for p in self.protocols if link.lower().startswith(f"{p}://")), 'unknown')
        return {'link': link, 'country': country, 'protocol': proto}

    async def run(self):
        all_links = set()
        for f_name in os.listdir(self.input_dir):
            if f_name.endswith('.txt'):
                with open(os.path.join(self.input_dir, f_name), 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if '://' in line: all_links.add(line.strip())
        
        print(f"[ТАМОЖНЯ] Обрабатываю {len(all_links)} строк...")
        async with aiohttp.ClientSession() as session:
            tasks = [self.process_link(session, link) for link in all_links]
            results = await asyncio.gather(*tasks)
        
        self.save_cache()
        warehouse = {}
        for res in results:
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
        print("[ТАМОЖНЯ] Работа завершена!")

if __name__ == "__main__":
    asyncio.run(CountrySorter().run())
