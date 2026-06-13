import os
import re
import sys
import time
import hashlib
import requests
import yaml
import json
import base64
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode, unquote

class Main1TelegramCollector:
    def __init__(self):
        # --- НАСТРОЙКА ПАРАЛЛЕЛЬНЫХ ОКОН (0 - 6) ---
        parser = argparse.ArgumentParser(description="Завод: Индустриальный Сборщик Телеграма main1.py")
        parser.add_argument('--window', type=int, default=0, help="Индекс параллельного окна (0-6)")
        parser.add_argument('--chunk-size', type=int, default=2500, help="Размер куска для рабочих окон")
        args, _ = parser.parse_known_args()
        
        self.window_id = args.window
        self.chunk_size = args.chunk_size

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

        # Пути распределения Завода
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources1.txt')
        self.amnezia_out_dir = os.path.join(self.base_dir, 'data', 'unique', 'AmneziaWG')
        self.throne_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.v2rayn_dir = os.path.join(self.base_dir, 'data', 'v2rayN')
        
        # Логи аудита пропусков и хэш-база
        self.hash_db_file = os.path.join(self.base_dir, 'data', 'sources', 'raw_hashes.txt')
        self.missed_log_file = os.path.join(self.base_dir, 'data', 'sources', 'missed_links.txt')
        # -------------------------------------

        self.max_file_size_mb = 40
        self.protocols = [
            'amneziawg', 'Xray VLESS', 'vless', 'wireguard', 'wg', 'hysteria2', 'hy2',
            'naive+https', 'shadowtls', 'trusttunnel', 'juicity', 'socks5', 'socks4', 
            'anytls', 'vmess', 'trojan', 'naive', 'socks', 'https', 'http', 'tuic', 'ssh', 'ss'
        ]
        
        search_protocols = [p for p in self.protocols if p not in ['Xray VLESS', 'amneziawg']]
        proto_pattern = '|'.join([re.escape(p) for p in search_protocols])
        # Регулярка агрессивно забирает всё из любого места текста, сообщений и блоков "Копировать"
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')
        
        self.raw_hashes = set()
        self.load_raw_hashes()
        self.sources = self.load_sources()

    def load_raw_hashes(self):
        if os.path.exists(self.hash_db_file):
            with open(self.hash_db_file, 'r', encoding='utf-8') as f:
                self.raw_hashes = set([line.strip() for line in f if line.strip()])

    def save_raw_hash(self, file_hash):
        self.raw_hashes.add(file_hash)
        os.makedirs(os.path.dirname(self.hash_db_file), exist_ok=True)
        with open(self.hash_db_file, 'a', encoding='utf-8') as f:
            f.write(file_hash + "\n")

    def load_sources(self):
        if not os.path.exists(self.sources_file): 
            print(f"⚠️ Ошибка: Файл источников {self.sources_file} не найден!", flush=True)
            return []
            
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip().startswith('http')]
        
        # 👑 РЕЖИМ ТОТАЛЬНОГО РАЗВЕДЧИКА ДЛЯ ОКНА №0
        if self.window_id == 0:
            print(f"🕵️‍♀️ [МАЙН1 ОКНО №0] РЕЖИМ ГЛУБОКОГО АНАЛИЗА: Загружена вся база ({len(lines)} источников)!", flush=True)
            return lines

        # ⚙️ РАБОЧИЕ ОКНА (1 - 6) пилят общую базу по кускам
        worker_index = self.window_id - 1
        start_idx = worker_index * self.chunk_size
        end_idx = start_idx + self.chunk_size
        sliced_sources = lines[start_idx:end_idx]

        print(f"📋 [МАЙН1 ОКНО №{self.window_id}] Потоковый сборщик открытых протоколов...")
        print(f"📐 Нарезка: {start_idx} -> {end_idx} | Взято: {len(sliced_sources)} источников", flush=True)
        return sliced_sources

    def get_unique_path(self, filename, text_content):
        cleaned_text = text_content.strip()
        new_hash = hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()

        if new_hash in self.raw_hashes:
            return None

        os.makedirs(self.amnezia_out_dir, exist_ok=True)
        name, ext = os.path.splitext(filename)
        target_path = os.path.join(self.amnezia_out_dir, filename)
        
        counter = 1
        while os.path.exists(target_path):
            target_path = os.path.join(self.amnezia_out_dir, f"{name}({counter}){ext}")
            counter += 1

        self.save_raw_hash(new_hash)
        return target_path

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

    def process_content(self, text, origin_url=None):
        if 'proxies:' in text: return self.parse_clash_yaml(text)
        extracted = []
        
        # Чтение .conf файлов (AmneziaWG/WireGuard)
        if "[interface]" in text.lower() and "[peer]" in text.lower():
            endpoint_match = re.search(r'(?i)^\s*Endpoint\s*=\s*([^\s#]+)', text, re.MULTILINE)
            if endpoint_match:
                endpoint = endpoint_match.group(1).strip()
                is_amnezia = any(k in text.lower() for k in ['jc =', 'jmin =', 'jmax =', 's1 =', 's2 ='])
                
                filename = "WARPv3_79.conf"
                if origin_url and origin_url.split('/')[-1].lower().endswith('.conf'):
                    filename = unquote(origin_url.split('/')[-1])

                target_path = self.get_unique_path(filename, text)
                if target_path:
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    prefix = "amneziawg" if is_amnezia else "wireguard"
                    extracted.append(f"{prefix}://{endpoint}#Raw_{os.path.basename(target_path).replace('.', '_')}")
        
        # Сбор строк прокси прямо из текста (для ss://, vless://, в том числе из спойлеров и кнопок скопировать)
        standard_links = [link.strip().rstrip('.') for link in self.regex_pattern.findall(text) 
                          if not any(bad in link for bad in ['User-Agent', 'headers', 'Pragma', 'cache-control', 'Host,'])]
        extracted.extend(standard_links)
        return extracted

    def extract_country(self, line):
        if '#' in line:
            tag = line.split('#')[-1].upper()
            for code in ['US', 'DE', 'NL', 'FR', 'GB', 'RU', 'UA', 'JP', 'KR', 'SG', 'HK', 'CN', 'FI', 'TR', 'PL', 'IR']:
                if code in tag: return code
            match = re.search(r'\b[A-Z]{2}\b', tag)
            if match: return match.group(0)
        return 'WORLD'

    def split_and_save_file(self, target_dir, base_name, lines):
        if not lines: return
        os.makedirs(target_dir, exist_ok=True)
        
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
            name = f"{base_name}.txt" if idx == 0 else f"{base_name}_{idx}.txt"
            with open(os.path.join(target_dir, name), 'a', encoding='utf-8') as pf:
                pf.write("\n".join(chunk_lines) + "\n")

    def collect(self):
        sys.stdout.reconfigure(line_buffering=True)
        if not self.sources: return
            
        print(f"🏭 [ЗАВОД ТГ] Старт Окна №{self.window_id}...", flush=True)
        collected, start_time = [], time.time()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'}
        missed_log = self.missed_log_file

        for i, url in enumerate(self.sources, 1):
            try:
                res = requests.get(url, headers=headers, timeout=12)
                if res.status_code == 200:
                    text_content = res.text
                    
                    # 1. Первичный сбор протоколов (Сюда автоматически попадает и замазанный текст!)
                    found_in_main = self.process_content(text_content, url)
                    collected.extend(found_in_main)
                    
                    # Инициализируем BeautifulSoup для поиска скрытых элементов оформления
                    soup = BeautifulSoup(text_content, 'html.parser')
                    
                    # 2. ДЕТЕКТОР "ЛОТЕРЕЙНЫХ" СПОЙЛЕРОВ И ЗАЧЁРКНУТОГО ТЕКСТА
                    # Ищем теги спойлеров <tg-spoiler>, зачёркивания <s>, <del> или специальные классы Телеграма
                    has_spoiler = soup.find(['tg-spoiler', 's', 'del']) or soup.find(class_=re.compile(r'spoiler|hidden'))
                    
                    # Если нашли признаки "замазанного" или зачёркнутого текста, но регулярка ничего не достала
                    if has_spoiler and not found_in_main:
                        os.makedirs(os.path.dirname(missed_log), exist_ok=True)
                        with open(missed_log, 'a', encoding='utf-8') as f:
                            f.write(f"[ОБНАРУЖЕН СКРЫТЫЙ ТЕКСТ / СПОЙЛЕР]: {url}\n")
                    
                    # 3. ОСОБАЯ ИНТЕЛЛЕКТУАЛЬНАЯ ЛОГИКА ДЛЯ ОКНА №0 (ПРОКЛИКИВАНИЕ)
                    if self.window_id == 0:
                        # Находим скрытые ссылки, подписки, вложения под кнопками (sub, clash, conf, txt)
                        sub_links = [urljoin(url, a['href'].strip()) for a in soup.find_all('a', href=True) 
                                     if any(k in a['href'].lower() for k in ['key=', 'sub', 'clash', '.txt', '.yaml', '.conf'])]
                        
                        # Кликаем (открываем) найденные скрытые окна и вкладки
                        for sub_url in list(set(sub_links))[:12]:
                            try:
                                s_res = requests.get(sub_url, headers=headers, timeout=10)
                                if s_res.status_code == 200:
                                    collected.extend(self.process_content(s_res.text, sub_url))
                            except: continue
                            
                        # Если совсем ничего не нашли, но есть триггерные слова — пишем в общий лог
                        if not found_in_main and not sub_links and not has_spoiler:
                            if any(trigger in text_content.lower() for trigger in ['vless://', 'ss://', 'trojan://', 'proxy']):
                                os.makedirs(os.path.dirname(missed_log), exist_ok=True)
                                with open(missed_log, 'a', encoding='utf-8') as f:
                                    f.write(f"[ПОДОЗРЕНИЕ НА СКРЫТОЕ ОКНО]: {url}\n")

                if self.window_id != 0 and (i % 50 == 0 or i == len(self.sources)):
                    print(f"📊 [ТГ Окно {self.window_id}] Пройдено: {i}/{len(self.sources)} | Собрано строк: {len(collected)}", flush=True)
                elif self.window_id == 0 and i % 10 == 0:
                    print(f"🕵️‍♀️ [РАЗВЕДЧИК №0] Глубокий анализ постов: {i}/{len(self.sources)}...", flush=True)
            except: continue

        # --- СОХРАНЕНИЕ И СОРТИРОВКА РЕЗУЛЬТАТОВ НА ЗАВОДЕ ---
        if collected:
            clean_list = sorted(list(set([l.strip() for l in collected if l.strip() and '://' in l])))
            
            for proto in self.protocols:
                if proto == 'Xray VLESS':
                    xray_lines = [l for l in clean_list if l.lower().startswith("vless://") and ('security=reality' in l.lower() or 'pbk=' in l.lower() or 'xtls' in l.lower())]
                    if xray_lines: self.split_and_save_file(self.throne_dir, 'Xray VLESS', xray_lines)
                elif proto == 'vless':
                    vless_lines = [l for l in clean_list if l.lower().startswith("vless://") and not ('security=reality' in l.lower() or 'pbk=' in l.lower() or 'xtls' in l.lower())]
                    if vless_lines: self.split_and_save_file(self.throne_dir, 'vless', vless_lines)
                else:
                    proto_lines = [l for l in clean_list if l.lower().startswith(f"{proto}://")]
                    if proto_lines: self.split_and_save_file(self.throne_dir, proto, proto_lines)

            v2rayn_bad_types = ('http://', 'https://', 'socks://', 'socks4://', 'socks5://')
            v2rayn_clean_list = [l for l in clean_list if not l.lower().startswith(v2rayn_bad_types)]

            country_map = {}
            for line in v2rayn_clean_list:
                if line.lower().startswith("amneziawg://"): 
                    line = line.replace("amneziawg://", "wireguard://")
                country = self.extract_country(line)
                if country not in country_map: country_map[country] = []
                country_map[country].append(line)

            for country, country_lines in country_map.items():
                self.split_and_save_file(self.v2rayn_dir, country, country_lines)

            print(f"🏁 [ФИНИШ: ОКНО {self.window_id}] Время работы: {time.time() - start_time:.2f} сек. Завод выдал максимум!", flush=True)

if __name__ == "__main__":
    Main1TelegramCollector().collect()
