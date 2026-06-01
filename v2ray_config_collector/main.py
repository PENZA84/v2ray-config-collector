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
            return []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip().startswith('http')]

    def parse_clash_yaml(self, yaml_text):
        extracted = []
        try:
            data = yaml.safe_load(yaml_text)
            if not data or 'proxies' not in data: return extracted
                
            for p in data['proxies']:
                if not isinstance(p, dict): continue
                p_type = str(p.get('type', '')).lower()
                name = str(p.get('name', 'Proxy')).replace(' ', '_')
                server, port = p.get('server'), p.get('port')
                uuid = str(p.get('uuid') or p.get('password', ''))
                
                if not server or not port: continue
                
                params = {}
                if p.get('network'): params['type'] = p.get('network')
                if p.get('tls'): params['security'] = 'tls'
                if p.get('servername'): params['sni'] = p.get('servername')
                if isinstance(p.get('ws-opts'), dict) and p['ws-opts'].get('path'): params['path'] = p['ws-opts']['path']
                if isinstance(p.get('grpc-opts'), dict) and p['grpc-opts'].get('grpc-service-name'): params['serviceName'] = p['grpc-opts']['grpc-service-name']

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
                    user_info = base64.b64encode(f"{p.get('cipher', 'aes-256-gcm')}:{uuid}".encode('utf-8')).decode('utf-8')
                    extracted.append(f"ss://{user_info}@{server}:{port}#{name}")
                elif p_type in self.protocols or p_type == 'hy2':
                    proto = 'hysteria2' if p_type == 'hy2' else p_type
                    extracted.append(f"{proto}://{uuid + '@' if uuid else ''}{server}:{port}#{name}")
        except Exception: pass
        return extracted

    def process_content(self, text):
        if 'proxies:' in text: return self.parse_clash_yaml(text)
        return [link.strip().rstrip('.') for link in self.regex_pattern.findall(text) 
                if not any(bad in link for bad in ['User-Agent', 'headers', 'Pragma', 'cache-control', 'Host,'])]

    def split_and_save_file(self, prefix, base_name, lines):
        if not lines: return
        full_name = f"{prefix}{base_name}"
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f.startswith(full_name) and f.endswith(".txt"):
                    try: os.remove(os.path.join(self.output_dir, f))
                    except: pass

        parts, current_chunk, current_size = [], [], 0
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
            name = f"{full_name}.txt" if idx == 0 else f"{full_name}_{idx}.txt"
            with open(os.path.join(self.output_dir, name), 'w', encoding='utf-8') as pf:
                pf.write("\n".join(chunk_lines) + "\n")

    def collect(self):
        sys.stdout.reconfigure(line_buffering=True)
        if not self.sources: return
            
        print(f"🏭 [MAIN] Запуск сбора ({len(self.sources)} источников)...", flush=True)
        collected, start_time = [], time.time()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'}

        for i, url in enumerate(self.sources, 1):
            try:
                res = requests.get(url, headers=headers, timeout=12)
                if res.status_code == 200:
                    if url.endswith(('.txt', '.yaml')) or '://' in res.text[:200]:
                        collected.extend(self.process_content(res.text))
                    else:
                        soup = BeautifulSoup(res.text, 'html.parser')
                        links = [urljoin(url, a['href'].strip()) for a in soup.find_all('a', href=True) 
                                 if any(k in a['href'].lower() for k in ['key=', 'sub', 'clash', '.txt', '.yaml'])]
                        for sub_url in list(set(links))[:8]:
                            try:
                                s_res = requests.get(sub_url, headers=headers, timeout=10)
                                if s_res.status_code == 200: collected.extend(self.process_content(s_res.text))
                            except: continue
                
                if i % 3 == 0 or i == len(self.sources):
                    print(f"📊 [Прогресс] {i}/{len(self.sources)} | Собрано: {len(collected)}", flush=True)
            except: continue

        if collected:
            clean = list(set([l.strip() for l in collected if l.strip() and '://' in l]))
            os.makedirs(self.output_dir, exist_ok=True)
            for proto in self.protocols:
                lines = [l for l in clean if l.lower().startswith(f"{proto}://")]
                if lines: self.split_and_save_file('', proto, lines)
            print(f"🏁 [INFO] Сбор завершен за {time.time() - start_time:.2f} сек!", flush=True)

if __name__ == "__main__":
    MainRawCollector().collect()
