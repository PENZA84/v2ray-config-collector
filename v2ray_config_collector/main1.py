import os
import re
import requests
import yaml
import json
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class TelegramRawCollector:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources1.txt')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.sources = self.load_sources()
        self.max_file_size_mb = 40 # С запасом по 40 МБ

    def load_sources(self):
        if not os.path.exists(self.sources_file): return []
        links = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('http'): links.append(line)
        print(f"📖 [main1.py] Загружено {len(links)} каналов из sources1.txt")
        return links

    def parse_clash_yaml(self, yaml_text):
        extracted = []
        try:
            data = yaml.safe_load(yaml_text)
            if not data or 'proxies' not in data: return extracted
            for p in data['proxies']:
                try:
                    p_type = str(p.get('type', '')).lower()
                    name = p.get('name', 'YAML_Proxy').replace(' ', '_')
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password')
                    if not server or not port: continue
                    if p_type == 'vless':
                        extracted.append(f"vless://{uuid}@{server}:{port}?type={p.get('network', 'tcp')}#{name}")
                    elif p_type == 'vmess':
                        v_json = {"v": "2", "ps": name, "add": server, "port": str(port), "id": uuid, "aid": "0", "net": p.get('network', 'tcp'), "type": "none", "host": "", "path": "", "tls": "tls" if p.get('tls') else ""}
                        extracted.append(f"vmess://{base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')}")
                    elif p_type == 'trojan':
                        extracted.append(f"trojan://{uuid}@{server}:{port}#{name}")
                    elif p_type == 'ss':
                        user_info = base64.b64encode(f"{p.get('cipher', 'aes-256-gcm')}:{uuid}".encode('utf-8')).decode('utf-8')
                        extracted.append(f"ss://{user_info}@{server}:{port}#{name}")
                except Exception: continue
        except Exception: pass
        return extracted

    def process_content(self, text):
        if 'proxies:' in text: return self.parse_clash_yaml(text)
        return re.findall(r'(?:vless|vmess|ss|trojan|naive|hysteria2|hy2|tuic|juicity)://[^\s<"\']+', text)

    def contains_markers(self, text):
        markers = ['vless://', 'vmess://', 'ss://', 'trojan://', 'proxies:', 'naive://', 'hysteria2://', 'hy2://', 'tuic://', 'juicity://']
        return any(m in text for m in markers)

    def split_and_save_file(self, prefix, base_name, lines):
        """✂️ Создание цепочки файлов ТГvless1.txt, ТГvless2.txt на лету"""
        if not lines: return
        
        full_base_name = f"{prefix}{base_name}"
        
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if re.match(r'^' + re.escape(full_base_name) + r'\d+\.txt$', f):
                    try: os.remove(os.path.join(self.output_dir, f))
                    except: pass

        current_part = 1
        current_lines = []
        current_size = 0
        
        for line in lines:
            line_bytes = (line + "\n").encode('utf-8')
            if current_size + len(line_bytes) > self.max_file_size_mb * 1024 * 1024:
                part_file = os.path.join(self.output_dir, f"{full_base_name}{current_part}.txt")
                with open(part_file, 'w', encoding='utf-8') as pf:
                    pf.write("\n".join(current_lines))
                print(f"📦 [ТГ-Цех] Создан кусок: {full_base_name}{current_part}.txt")
                current_part += 1
                current_lines = [line]
                current_size = len(line_bytes)
            else:
                current_lines.append(line)
                current_size += len(line_bytes)
                
        if current_lines:
            part_file = os.path.join(self.output_dir, f"{full_base_name}{current_part}.txt")
            with open(part_file, 'w', encoding='utf-8') as pf:
                pf.write("\n".join(current_lines))
            print(f"📦 [ТГ-Цех] Успешно сохранен: {full_base_name}{current_part}.txt ({len(current_lines)} строк)")

    def collect(self):
        if not self.sources: return
        collected = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        for url in self.sources:
            try:
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code != 200: continue
                content = res.text

                if url.endswith('.txt') or url.endswith('.yaml') or '://' in content[:200]:
                    collected.extend(self.process_content(content))
                    continue

                soup = BeautifulSoup(content, 'html.parser')
                found_links = []

                for box in soup.find_all(['textarea', 'code', 'input', 'pre', 'div']):
                    if box.name == 'div' and 'tgme_widget_message_text' not in str(box.get('class', [])): continue
                    val = box.get('value') or box.string or box.get_text()
                    if val: found_links.extend(re.findall(r'https?://[^\s<"\']+', str(val)))

                for a in soup.find_all('a', href=True): found_links.append(urljoin(url, a['href'].strip()))

                if self.contains_markers(content): collected.extend(self.process_content(content))

                for f_url in list(set(found_links))[:8]:
                    if f_url == url or 't.me' in f_url.lower() and '/s/' not in f_url.lower(): continue
                    try:
                        sub_res = requests.get(f_url, headers=headers, timeout=5)
                        if sub_res.status_code == 200 and self.contains_markers(sub_res.text):
                            collected.extend(self.process_content(sub_res.text))
                    except Exception: continue
            except Exception: continue

        if collected:
            clean = list(set([l.strip() for l in collected if l.strip()]))
            os.makedirs(self.output_dir, exist_ok=True)
            
            existing = []
            if os.path.exists(self.output_dir):
                for f in sorted(os.listdir(self.output_dir)):
                    if re.match(r'^ТГdeduplicated\d+\.txt$', f):
                        try:
                            with open(os.path.join(self.output_dir, f), 'r', encoding='utf-8') as pf:
                                existing.extend([line.strip() for line in pf if line.strip()])
                        except: pass
            
            total = list(set(existing + clean))
            
            # Сохраняем ТГ базы только с номерами и меткой ТГ
            self.split_and_save_file('ТГ', 'deduplicated', total)

            protocols = ['vless', 'vmess', 'ss', 'trojan', 'naive', 'hysteria2', 'hy2', 'tuic', 'juicity']
            for proto in protocols:
                proto_lines = [l for l in total if l.lower().startswith(f"{proto}://")]
                self.split_and_save_file('ТГ', proto, proto_lines)
                
            print(f"🏁 [main1.py] ТГ-Цех отработал успешно!")

if __name__ == "__main__":
    TelegramRawCollector().collect()
