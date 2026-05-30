import os
import re
import sys
import time
import requests
import yaml
import json
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode

class MainRawCollector:
    def __init__(self):
        # --- ИСПРАВЛЕННАЯ НАВИГАЦИЯ ---
        current_file_path = os.path.abspath(__file__)
        self.base_dir = os.path.dirname(current_file_path)
        
        if os.path.basename(self.base_dir) == 'core':
            self.base_dir = os.path.dirname(self.base_dir)
            
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources.txt')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        # ------------------------------

        self.max_file_size_mb = 40
        
        self.protocols = [
            'naive+https', 'shadowtls', 'trusttunnel', 'hysteria2', 'wireguard', 
            'juicity', 'socks5', 'socks4', 'anytls', 'vmess', 'vless', 'trojan', 
            'naive', 'socks', 'https', 'http', 'tuic', 'hy2', 'ssh', 'wg', 'ss'
        ]
        
        proto_pattern = '|'.join([re.escape(p) for p in self.protocols])
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')
        
        self.sources = self.load_sources()

    def load_sources(self):
        if not os.path.exists(self.sources_file): 
            print(f"❌ ОШИБКА: Файл источников не найден по пути: {self.sources_file}", flush=True)
            return []
        links = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('http'): 
                    links.append(line)
        return links

    def parse_clash_yaml(self, yaml_text):
        extracted = []
        try:
            data = yaml.safe_load(yaml_text)
            # --- ИСПРАВЛЕНО ТУТ: УБРАН ДВОЙНОЙ 'not not' ---
            if not data or 'proxies' not in data: 
                return extracted
                
            for p in data['proxies']:
                try:
                    if not isinstance(p, dict): 
                        continue
                    p_type = str(p.get('type', '')).lower()
                    name = str(p.get('name', 'Proxy')).replace(' ', '_')
                    server = p.get('server')
                    port = p.get('port')
                    raw_uuid = p.get('uuid') or p.get('password')
                    uuid = str(raw_uuid) if raw_uuid is not None else None
                    
                    if not server or not port: 
                        continue
                    
                    params = {}
                    if p.get('network'): params['type'] = p.get('network')
                    if p.get('tls'): params['security'] = 'tls'
                    if p.get('servername'): params['sni'] = p.get('servername')
                    if p.get('ws-opts') and isinstance(p['ws-opts'], dict):
                        ws_path = p['ws-opts'].get('path')
                        if ws_path: params['path'] = ws_path
                    if p.get('grpc-opts') and isinstance(p['grpc-opts'], dict):
                        grpc_name = p['grpc-opts'].get('grpc-service-name')
                        if grpc_name: params['serviceName'] = grpc_name

                    param_str = f"?{urlencode(params)}" if params else ""

                    if p_type == 'vless' and uuid:
                        extracted.append(f"vless://{uuid}@{server}:{port}{param_str}#{name}")
                    elif p_type == 'vmess' and uuid:
                        v_json = {
                            "v": "2", "ps": name, "add": str(server), "port": str(port), 
                            "id": uuid, "aid": "0", "net": p.get('network', 'tcp'), 
                            "type": "none", "host": p.get('servername', ''), 
                            "path": p.get('ws-opts', {}).get('path', '') if isinstance(p.get('ws-opts'), dict) else '', 
                            "tls": "tls" if p.get('tls') else ""
                        }
                        encoded = base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')
                        extracted.append(f"vmess://{encoded}")
                    elif p_type == 'trojan' and uuid:
                        extracted.append(f"trojan://{uuid}@{server}:{port}{param_str}#{name}")
                    elif p_type == 'ss' and uuid:
                        cipher = p.get('cipher', 'aes-256-gcm')
                        user_info = base64.b64encode(f"{cipher}:{uuid}".encode('utf-8')).decode('utf-8')
                        extracted.append(f"ss://{user_info}@{server}:{port}#{name}")
                    elif p_type in self.protocols or f"{p_type}" in ['hy2']:
                        proto_name = 'hysteria2' if p_type == 'hy2' else p_type
                        user_part = f"{uuid}@" if uuid else ""
                        extracted.append(f"{proto_name}://{user_part}{server}:{port}#{name}")
                except Exception: 
                    continue
        except Exception: 
            pass
        return extracted

    def process_content(self, text):
        if 'proxies:' in text: 
            return self.parse_clash_yaml(text)
        found = self.regex_pattern.findall(text)
        clean_found = []
        for link in found:
            link = link.strip().rstrip('.')
            if any(bad in link for bad in ['User-Agent', 'headers', 'Pragma', 'cache-control', 'Host,']):
                continue
            clean_found.append(link)
        return clean_found

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
            print("⚠️ Список источников в sources.txt пуст или файл не найден.", flush=True)
            return
            
        print(f"🏭 Основной Цех Завода запускает всеядный сбор...", flush=True)
        print(f"📍 СКЛАД БУДЕТ ЗДЕСЬ: {self.output_dir}", flush=True)
        
        collected = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'}
        start_time = time.time()
        processed_sources = 0

        for url in self.sources:
            processed_sources += 1
            try:
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200: continue
                content = res.text
                
                if url.endswith('.txt') or url.endswith('.yaml') or '://' in content[:200]:
                    parsed_links = self.process_content(content)
                    collected.extend(parsed_links)
                else:
                    soup = BeautifulSoup(content, 'html.parser')
                    links = [urljoin(url, a['href'].strip()) for a in soup.find_all('a', href=True) if any(k in a['href'].lower() for k in ['key=', 'sub', 'clash', '.txt', '.yaml'])]
                    for sub_url in list(set(links))[:8]:
                        try:
                            s_res = requests.get(sub_url, headers=headers, timeout=10)
                            if s_res.status_code == 200: 
                                collected.extend(self.process_content(s_res.text))
                        except: continue

                if processed_sources % 3 == 0 or processed_sources == len(self.sources):
                    elapsed = time.time() - start_time
                    speed = int(len(collected) / elapsed) if elapsed > 0 else 0
                    print(f"📊 [Прогресс] Источников: {processed_sources}/{len(self.sources)} | Собрано: {len(collected)} | Скорость: {speed} л/сек", flush=True)
            except: continue

        if collected:
            total_raw = len(collected)
            print("\n⚙️ Запуск очистки и распределения...", flush=True)
            clean = list(set([l.strip() for l in collected if l.strip() and '://' in l]))
            duplicate_count = total_raw - len(clean)
            print(f"🗑️ Дубликатов удалено: {duplicate_count} | 💎 Чистых: {len(clean)}", flush=True)
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            for proto in self.protocols:
                proto_lines = [l for l in clean if l.lower().startswith(f"{proto}://")]
                if proto_lines:
                    self.split_and_save_file('', proto, proto_lines)
                    
            total_time = time.time() - start_time
            print(f"\n🏁 [INFO] [MAIN] Успешно завершено за {total_time:.2f} сек!", flush=True)
            print(f"✅ Файлы протоколов обновлены в: {self.output_dir}", flush=True)
        else:
            print("❌ Сбор завершен. Данные не найдены.", flush=True)

if __name__ == "__main__":
    MainRawCollector().collect()
