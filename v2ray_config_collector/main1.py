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
        # 🎯 СТРОГО СВОЙ СПИСОК ИСТОЧНИКОВ!
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources1.txt')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_file = os.path.join(self.output_dir, 'deduplicated.txt')
        self.sources = self.load_sources()

    def load_sources(self):
        if not os.path.exists(self.sources_file):
            print(f"⚠️ [main1.py] Файл источников не найден: {self.sources_file}")
            return []
        links = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('http'): links.append(line)
        print(f"📖 [main1.py] Загружено {len(links)} Телеграм-каналов/ссылок из sources1.txt")
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
        return any(m in text for m in ['vless://', 'vmess://', 'ss://', 'trojan://', 'proxies:', 'naive://'])

    def collect(self):
        if not self.sources: return
        collected = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        for url in self.sources:
            try:
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code != 200: continue
                content = res.text

                # Если прямая ссылка на RAW-файл - забираем сразу
                if url.endswith('.txt') or url.endswith('.yaml') or '://' in content[:200]:
                    collected.extend(self.process_content(content))
                    continue

                soup = BeautifulSoup(content, 'html.parser')
                found_links = []

                # 🎯 ДОСТАЕМ СКРЫТЫЕ ССЫЛКИ ИЗ КОРОВОК И ТЕЛЕГРАМ-ПОСТОВ
                for box in soup.find_all(['textarea', 'code', 'input', 'pre', 'div']):
                    if box.name == 'div' and 'tgme_widget_message_text' not in str(box.get('class', [])): 
                        continue
                    val = box.get('value') or box.string or box.get_text()
                    if val:
                        # Парсим любые http/https ссылки внутри текстовых блоков
                        found_links.extend(re.findall(r'https?://[^\s<"\']+', str(val)))

                # Собираем обычные ссылки со страницы
                for a in soup.find_all('a', href=True):
                    found_links.append(urljoin(url, a['href'].strip()))

                # Если в самом посте или на странице есть готовые прокси - берем их
                if self.contains_markers(content):
                    collected.extend(self.process_content(content))

                # 🚀 ПЕРЕХОД ПО ССЫЛКАМ ИЗ КОРОВОК (Внутрь скрытых файлов .txt / .yaml)
                for f_url in list(set(found_links))[:8]:
                    if f_url == url or 't.me' in f_url.lower() and '/s/' not in f_url.lower(): 
                        continue
                    try:
                        sub_res = requests.get(f_url, headers=headers, timeout=5)
                        if sub_res.status_code == 200 and self.contains_markers(sub_res.text):
                            collected.extend(self.process_content(sub_res.text))
                    except Exception: 
                        continue
            except Exception: 
                continue

        self.save_and_sort(collected)

    def save_and_sort(self, lines):
        if not lines: return
        clean = list(set([l.strip() for l in lines if l.strip()]))
        existing = []
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                existing = [line.strip() for line in f if line.strip()]
        
        total = list(set(existing + clean))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Пишем в общий котел deduplicated.txt
        with open(self.output_file, 'w', encoding='utf-8') as f: 
            f.write("\n".join(total))

        # 🪐 ТВОЯ НОВАЯ СОРТИРОВКА ДЛЯ ТРОНА И ОБНОВЛЕННОГО v2rayN ПО ФАЙЛАМ
        protocols = ['vless', 'vmess', 'ss', 'trojan', 'naive', 'hysteria2', 'hy2', 'tuic', 'juicity']
        for proto in protocols:
            proto_lines = [l for l in total if l.lower().startswith(f"{proto}://")]
            with open(os.path.join(self.output_dir, f"{proto}.txt"), 'w', encoding='utf-8') as pf:
                pf.write("\n".join(proto_lines))
        print(f"🏁 [main1.py] ТГ-Цех успешно отработал! Все файлы протоколов, включая naive.txt, обновлены!")

if __name__ == "__main__":
    TelegramRawCollector().collect()
