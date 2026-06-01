import os
import re
import sys
import time
import requests
from urllib.parse import urlparse, parse_qs

class TelegramRawCollector:
    def __init__(self):
        # --- МОНОЛИТНАЯ НАВИГАЦИЯ ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        self.base_dir = current_dir
        found_root = False
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                found_root = True
                break
            self.base_dir = os.path.dirname(self.base_dir)
        
        if not found_root:
            self.base_dir = current_dir

        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources1.txt')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        # -----------------------------

        self.max_file_size_mb = 40
        self.protocols = [
            'socks5', 'socks4', 'socks', 'http', 'https', 'ss', 'trojan', 
            'vmess', 'vless', 'tuic', 'hysteria', 'hysteria2', 'hy2', 
            'anytls', 'naive', 'naive+https', 'juicity', 'trusttunnel', 
            'shadowtls', 'wireguard', 'wg', 'ssh'
        ]
        
        proto_pattern = '|'.join([re.escape(p) for p in self.protocols])
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')
        self.tg_proxy_pattern = re.compile(r'(?:https://t.me/proxy?[^s<"\']+)|(?:tg://proxy\?[^\s<"\']*)')
        
        self.sources = self.load_sources()

    def load_sources(self):
        if not os.path.exists(self.sources_file): 
            return []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip().startswith('http')]

    def process_content(self, text):
        extracted = []
        found_profiles = self.regex_pattern.findall(text)
        for link in found_profiles:
            link = link.strip().rstrip('.')
            if any(bad in link for bad in ['User-Agent', 'headers', 'Pragma', 'cache-control', 'Host,']):
                continue
            extracted.append(link)
        
        tg_proxies = self.tg_proxy_pattern.findall(text.replace('&amp;', '&'))
        for tg_url in tg_proxies:
            try:
                parsed = urlparse(tg_url)
                query = parse_qs(parsed.query)
                server = query.get('server', [None])[0]
                port = query.get('port', [None])[0]
                if server and port:
                    extracted.append(f"socks5://{server}:{port}#TG_Socks")
                    extracted.append(f"http://{server}:{port}#TG_HTTP")
            except: continue
        return extracted

    def split_and_save_file(self, prefix, base_name, lines):
        if not lines: return
        full_base_name = f"{prefix}{base_name}"
        
        # Очистка старых файлов перед записью новых (заводской стандарт)
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f.startswith(f"{full_base_name}") and f.endswith(".txt"):
                    try: os.remove(os.path.join(self.output_dir, f))
                    except: pass

        parts = []
        current_chunk, current_size = [], 0
        max_bytes = self.max_file_size_mb * 1024 * 1024

        for line in lines:
            line_bytes = (line + "\n").encode('utf-8')
            if current_size + len(line_bytes) > max_bytes and current_chunk:
                parts.append(current_chunk)
                current_chunk, current_size = [line], len(line_bytes)
            else:
                current_chunk.append(line)
                current_size += len(line_bytes)
        if current_chunk: parts.append(current_chunk)

        for idx, chunk_lines in enumerate(parts):
            name = f"{full_base_name}.txt" if idx == 0 else f"{full_base_name}_{idx}.txt"
            with open(os.path.join(self.output_dir, name), 'w', encoding='utf-8') as pf:
                pf.write("\n".join(chunk_lines) + "\n")

    def collect(self):
        sys.stdout.reconfigure(line_buffering=True)
        if not self.sources: return
            
        print(f"🏭 [TG_MAIN] Запуск сбора ({len(self.sources)} источников)...", flush=True)
        
        collected = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'}
        start_time = time.time()
        
        for i, url in enumerate(self.sources, 1):
            try:
                res = requests.get(url, headers=headers, timeout=12) # Чуть больше таймаут для стабильности
                if res.status_code == 200:
                    collected.extend(self.process_content(res.text))
                if i % 5 == 0 or i == len(self.sources):
                    print(f"📊 [Прогресс] {i}/{len(self.sources)} | Собрано: {len(collected)}", flush=True)
            except: continue

        if collected:
            clean = list(set([l.strip() for l in collected if l.strip()]))
            print(f"💎 Чистых конфигов: {len(clean)}", flush=True)
            
            os.makedirs(self.output_dir, exist_ok=True)
            for proto in self.protocols:
                proto_lines = [l for l in clean if l.lower().startswith(f"{proto}://")]
                if proto_lines:
                    self.split_and_save_file('ТГ_', proto, proto_lines)
            print(f"🏁 [INFO] Сбор завершен за {time.time() - start_time:.2f} сек!", flush=True)

if __name__ == "__main__":
    TelegramRawCollector().collect()
