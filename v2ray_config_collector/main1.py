import os
import re
import sys
import time
import requests
from urllib.parse import urlparse, parse_qs

class TelegramRawCollector:
    def __init__(self):
        # --- МОНОЛИТНАЯ НАВИГАЦИЯ (СИНХРОНИЗАЦИЯ С ЗАВОДОМ) ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        # Ищем корень проекта по наличию папки 'data'
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
        # -------------------------------------------------------

        self.max_file_size_mb = 40
        
        self.protocols = [
            'socks5', 'socks4', 'socks', 'http', 'https', 'ss', 'trojan', 
            'vmess', 'vless', 'tuic', 'hysteria', 'hysteria2', 'hy2', 
            'anytls', 'naive', 'naive+https', 'juicity', 'trusttunnel', 
            'shadowtls', 'wireguard', 'wg', 'ssh'
        ]
        
        proto_pattern = '|'.join([re.escape(p) for p in self.protocols])
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')
        self.tg_proxy_pattern = re.compile(r'(?:https://t\.me/proxy\?[^\s<"\']+)|(?:tg://proxy\?[^\s<"\']*)')
        
        self.sources = self.load_sources()

    def load_sources(self):
        if not os.path.exists(self.sources_file): 
            print(f"❌ ОШИБКА: Файл источников не найден: {self.sources_file}", flush=True)
            return []
        links = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('http'): 
                    links.append(line)
        return links

    def process_content(self, text):
        extracted = []
        found_profiles = self.regex_pattern.findall(text)
        for link in found_profiles:
            link = link.strip().rstrip('.')
            if any(bad in link for bad in ['User-Agent', 'headers', 'Pragma', 'cache-control', 'Host,']):
                continue
            extracted.append(link)
        
        clean_text = text.replace('&amp;', '&')
        tg_proxies = self.tg_proxy_pattern.findall(clean_text)
        
        for tg_url in tg_proxies:
            try:
                parsed = urlparse(tg_url)
                query = parse_qs(parsed.query)
                server = query.get('server', [None])[0]
                port = query.get('port', [None])[0]
                if server and port:
                    extracted.append(f"socks5://{server}:{port}#TG_Socks")
                    extracted.append(f"http://{server}:{port}#TG_HTTP")
            except:
                continue
        return extracted

    def split_and_save_file(self, prefix, base_name, lines):
        if not lines: 
            return
        full_base_name = f"{prefix}{base_name}"
        
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f == f"{full_base_name}.txt" or re.match(r'^' + re.escape(full_base_name) + r'_\d+\.txt$', f):
                    try: os.remove(os.path.join(self.output_dir, f))
                    except: pass

        parts = []
        current_chunk = []
        current_size = 0
        max_bytes = self.max_file_size_mb * 1024 * 1024

        for line in lines:
            line_bytes = (line + "\n").encode('utf-8')
            if current_size + len(line_bytes) > max_bytes and current_chunk:
                parts.append(current_chunk)
                current_chunk = [line]
                current_size = len(line_bytes)
            else:
                current_chunk.append(line)
                current_size += len(line_bytes)
        if current_chunk:
            parts.append(current_chunk)

        for idx, chunk_lines in enumerate(parts):
            if idx == 0:
                part_file = os.path.join(self.output_dir, f"{full_base_name}.txt")
            else:
                part_file = os.path.join(self.output_dir, f"{full_base_name}_{idx}.txt")
            with open(part_file, 'w', encoding='utf-8') as pf:
                pf.write("\n".join(chunk_lines) + "\n")

    def collect(self):
        sys.stdout.reconfigure(line_buffering=True)
        if not self.sources: 
            print("⚠️ Список источников в sources1.txt пуст или файл не найден.", flush=True)
            return
            
        print(f"🏭 Телеграм-Цех Завода запускает сбор (Всего источников: {len(self.sources)})...", flush=True)
        print(f"📍 СКЛАД БУДЕТ ЗДЕСЬ: {self.output_dir}", flush=True)
        
        collected = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'}
        start_time = time.time()
        processed_channels = 0
        
        for url in self.sources:
            processed_channels += 1
            try:
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200: continue
                new_configs = self.process_content(res.text)
                collected.extend(new_configs)
                if processed_channels % 5 == 0 or processed_channels == len(self.sources):
                    elapsed = time.time() - start_time
                    speed = int(len(collected) / elapsed) if elapsed > 0 else 0
                    print(f"📊 [Прогресс ТГ] Обработано каналов: {processed_channels}/{len(self.sources)} | Собрано: {len(collected)} | Скорость: {speed} л/сек", flush=True)
            except: continue

        if collected:
            total_raw = len(collected)
            print("\n⚙️ Запуск фильтрации дубликатов...", flush=True)
            clean = list(set([l.strip() for l in collected if l.strip()]))
            duplicate_count = total_raw - len(clean)
            print(f"🗑️ Удалено дубликатов: {duplicate_count} | 💎 Чистых: {len(clean)}", flush=True)
            
            os.makedirs(self.output_dir, exist_ok=True)
            for proto in self.protocols:
                proto_lines = [l for l in clean if l.lower().startswith(f"{proto}://")]
                if proto_lines:
                    self.split_and_save_file('ТГ_', proto, proto_lines)
                    
            total_time = time.time() - start_time
            print(f"\n🏁 [INFO] [TG_MAIN] Сбор завершен за {total_time:.2f} сек!", flush=True)
        else:
            print("❌ Ни одной конфигурации не найдено.", flush=True)

if __name__ == "__main__":
    TelegramRawCollector().collect()
