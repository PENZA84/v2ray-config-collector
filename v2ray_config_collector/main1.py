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
        self.max_file_size_mb = 40

    def load_sources(self):
        if not os.path.exists(self.sources_file): return []
        links = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('http'): links.append(line)
        return links

    def process_content(self, text):
        return re.findall(r'(?:vless|vmess|ss|trojan|naive|hysteria2|hy2|tuic|juicity)://[^\s<"\']+', text)

    def split_and_save_file(self, prefix, base_name, lines):
        if not lines: return
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
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code != 200: continue
                content = res.text
                if url.endswith('.txt') or '://' in content[:200]:
                    collected.extend(self.process_content(content))
                    continue
                
                protocols_to_check = ['vless://', 'vmess://', 'ss://', 'trojan://', 'naive://', 'hysteria2://', 'hy2://', 'tuic://', 'juicity://']
                if any(m in content for m in protocols_to_check):
                    collected.extend(self.process_content(content))
            except: continue

        if collected:
            clean = list(set([l.strip() for l in collected if l.strip() and '://' in l]))
            os.makedirs(self.output_dir, exist_ok=True)
            self.split_and_save_file('ТГ ', 'deduplicated', clean)
            
            for proto in ['vless', 'vmess', 'ss', 'trojan', 'naive', 'hysteria2', 'hy2', 'tuic', 'juicity']:
                proto_lines = [l for l in clean if l.lower().startswith(f"{proto}://")]
                if proto_lines:
                    self.split_and_save_file('ТГ ', proto, proto_lines)

if __name__ == "__main__":
    TelegramRawCollector().collect()
