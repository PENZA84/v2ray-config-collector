import os
import re
import requests
import yaml
import json
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class MainRawCollector:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources.txt')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.sources = self.load_sources()
        self.max_file_size_mb = 40  # Твой лимит 40 МБ

    def load_sources(self):
        if not os.path.exists(self.sources_file): return []
        links = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('http'): links.append(line)
        return links

    def parse_clash_yaml(self, yaml_text):
        extracted = []
        try:
            data = yaml.safe_load(yaml_text)
            if not data or 'proxies' not in data: return extracted
            for p in data['proxies']:
                try:
                    p_type = str(p.get('type', '')).lower()
                    name = p.get('name', 'Proxy').replace(' ', '_')
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password')
                    if not server or not port: continue
                    if p_type == 'vless':
                        link = f"vless://{uuid}@{server}:{port}?type={p.get('network', 'tcp')}"
                        if p.get('tls'): link += "&security=tls"
                        extracted.append(f"{link}#{name}")
                    elif p_type == 'vmess':
                        v_json = {"v": "2", "ps": name, "add": server, "port": str(port), "id": uuid, "aid": "0", "net": p.get('network', 'tcp'), "type": "none", "host": "", "path": "", "tls": "tls" if p.get('tls') else ""}
                        # ТУТ ИСПРАВЛЕНО: Строго vmess:// вместо vless://
                        extracted.append(f"vmess://{base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')}")
                    elif p_type == 'trojan':
                        extracted.append(f"trojan://{uuid}@{server}:{port}#{name}")
                    elif p_type == 'ss':
                        cipher = p.get('cipher', 'aes-256-gcm')
                        user_info = base64.b64encode(f"{cipher}:{uuid}".encode('utf-8')).decode('utf-8')
                        extracted.append(f"ss://{user_info}@{server}:{port}#{name}")
                except Exception: continue
        except Exception: pass
        return extracted

    def process_content(self, text):
        if 'proxies:' in text: return self.parse_clash_yaml(text)
        return re.findall(r'(?:vless|vmess|ss|trojan|naive|hysteria2|hy2|tuic|juicity)://[^\s<"\']+', text)

    def split_and_save_file(self, prefix, base_name, lines):
        if not lines: return  # Если прокси нет — пустой файл не создаем, чтобы гитхаб не тупил при скачивании
        full_base_name = f"{prefix}{base_name}"
        
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f == f"{full_base_name}.txt" or re.match(r'^' + re.escape(full_base_name) + r'\s+\d+\.txt$', f):
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

        # ТУТ ИСПРАВЛЕНО: Строго один пробел перед цифрой (vless.txt, vless 1.txt, vless 2.txt)
        for idx, chunk_lines in enumerate(parts):
            if idx == 0:
                part_file = os.path.join(self.output_dir, f"{full_base_name}.txt")
            else:
                part_file = os.path.join(self.output_dir, f"{full_base_name} {idx}.txt")
            
            with open(part_file, 'w', encoding='utf-8') as pf:
                pf.write("\n".join(chunk_lines))

    def collect(self):
        if not self.sources: return
        collected = []
        headers = {'User-Agent': 'Mozilla/5.0'}
        for url in self.sources:
            try:
                res = requests.get(url, headers=headers, timeout=4)
                if res.status_code != 200: continue
                content = res.text
                if url.endswith('.txt') or url.endswith('.yaml') or '://' in content[:200]:
                    collected.extend(self.process_content(content))
                    continue
                soup = BeautifulSoup(content, 'html.parser')
                links = [urljoin(url, a['href'].strip()) for a in soup.find_all('a', href=True) if any(k in a['href'].lower() for k in ['key=', 'sub', 'clash', '.txt'])]
                for sub_url in list(set(links))[:6]:
                    try:
                        s_res = requests.get(sub_url, headers=headers, timeout=4)
                        if s_res.status_code == 200: collected.extend(self.process_content(s_res.text))
                    except: continue
            except: continue

        if collected:
            clean = list(set([l.strip() for l in collected if l.strip() and '://' in l]))
            os.makedirs(self.output_dir, exist_ok=True)
            self.split_and_save_file('', 'deduplicated', clean)
            for proto in ['vless', 'vmess', 'ss', 'trojan', 'naive', 'hysteria2', 'hy2', 'tuic', 'juicity']:
                proto_lines = [l for l in clean if l.lower().startswith(f"{proto}://")]
                if proto_lines:
                    self.split_and_save_file('', proto, proto_lines)

if __name__ == "__main__":
    MainRawCollector().collect()
