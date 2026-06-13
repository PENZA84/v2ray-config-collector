import os
import re
import sys
import time
import hashlib
import requests
import yaml
import json
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode, quote, unquote

class MainRawCollector:
    def __init__(self):
        # --- МОНОЛИТНАЯ НАВИГАЦИЯ ЛЕИ ---
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

        # СТРОГО ОСНОВНОЙ RAW ФАЙЛ ИСТОЧНИКОВ
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources.txt')
        self.amnezia_out_dir = os.path.join(self.base_dir, 'data', 'unique', 'AmneziaWG')
        self.throne_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.v2rayn_dir = os.path.join(self.base_dir, 'data', 'v2rayN')
        
        # Изолированная текстовая база хэшей для одиночных файлов (Принцип Файл-Файл)
        self.hash_db_file = os.path.join(self.base_dir, 'data', 'sources', 'raw_hashes.txt')

        self.max_file_size_mb = 40
        self.protocols = [
            'amneziawg', 'Xray VLESS', 'vless', 'wireguard', 'wg', 'hysteria2', 'hy2',
            'naive+https', 'shadowtls', 'trusttunnel', 'juicity', 'socks5', 'socks4', 
            'anytls', 'vmess', 'trojan', 'naive', 'socks', 'https', 'http', 'tuic', 'ssh', 'ss'
        ]
        
        search_protocols = [p for p in self.protocols if p not in ['Xray VLESS', 'amneziawg']]
        proto_pattern = '|'.join([re.escape(p) for p in search_protocols])
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')
        
        self.raw_hashes = set()
        self.load_raw_hashes()
        self.sources = self.load_sources()

    def load_raw_hashes(self):
        """Загружает хэши ранее обработанных одиночных файлов"""
        if os.path.exists(self.hash_db_file):
            with open(self.hash_db_file, 'r', encoding='utf-8') as f:
                self.raw_hashes = set([line.strip() for line in f if line.strip()])

    def save_raw_hash(self, file_hash):
        """Сохраняет хэш нового файла в текстовую базу"""
        self.raw_hashes.add(file_hash)
        os.makedirs(os.path.dirname(self.hash_db_file), exist_ok=True)
        with open(self.hash_db_file, 'a', encoding='utf-8') as f:
            f.write(file_hash + "\n")

    def load_sources(self):
        if not os.path.exists(self.sources_file): 
            print(f"⚠️ Ошибка: Главный Raw-файл источников {self.sources_file} не найден!", flush=True)
            return []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip().startswith('http')]
        print(f"📋 [МАЙН RAW] Загружен базовый файл [sources.txt]. Найдено сырых ссылок: {len(lines)}", flush=True)
        return lines

    def get_unique_path(self, filename, text_content):
        """Принцип Файл-Файл: сверяет MD5 кода и создаёт индексы (1), (2) для обновлённых конфигов"""
        cleaned_text = text_content.strip()
        new_hash = hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()

        # Если код этого конфига уже скачивался напрямую — это дубликат, пропускаем его
        if new_hash in self.raw_hashes:
            return None

        os.makedirs(self.amnezia_out_dir, exist_ok=True)
        name, ext = os.path.splitext(filename)
        target_path = os.path.join(self.amnezia_out_dir, filename)
        
        counter = 1
        # Если имя занято, но внутри новый обновлённый контент — нарезаем индекс
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
        
        # Обнаружение конфигураций WireGuard и AmneziaWG
        if "[interface]" in text.lower() and "[peer]" in text.lower():
            endpoint_match = re.search(r'(?i)^\s*Endpoint\s*=\s*([^\s#]+)', text, re.MULTILINE)
            if endpoint_match:
                endpoint = endpoint_match.group(1).strip()
                is_amnezia = any(k in text.lower() for k in ['jc =', 'jmin =', 'jmax =', 's1 =', 's2 ='])
                
                filename = "WARPv3_79.conf"
                if origin_url and origin_url.split('/')[-1].lower().endswith('.conf'):
                    filename = unquote(origin_url.split('/')[-1])

                # Контроль Файл-Файл по уникальности хэша кода
                target_path = self.get_unique_path(filename, text)
                if target_path:
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    prefix = "amneziawg" if is_amnezia else "wireguard"
                    # В ссылку подставляем имя реально созданного на диске файла
                    extracted.append(f"{prefix}://{endpoint}#Raw_{os.path.basename(target_path).replace('.', '_')}")
        
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
        
        for f in os.listdir(target_dir):
            if f.startswith(base_name) and f.endswith(".txt"):
                try: os.remove(os.path.join(target_dir, f))
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
            name = f"{base_name}.txt" if idx == 0 else f"{base_name}_{idx}.txt"
            with open(os.path.join(target_dir, name), 'w', encoding='utf-8') as pf:
                pf.write("\n".join(chunk_lines) + "\n")

    def collect(self):
        sys.stdout.reconfigure(line_buffering=True)
        if not self.sources: return
            
        print(f"🏭 [ЗАВОД RAW] Запуск глобальной обработки сырых источников...", flush=True)
        collected, start_time = [], time.time()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'}

        for i, url in enumerate(self.sources, 1):
            try:
                if "github.com" in url.lower():
                    if "/blob/" in url.lower():
                        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                        res = requests.get(raw_url, headers=headers, timeout=12)
                        if res.status_code == 200: collected.extend(self.process_content(res.text, raw_url))
                    elif "raw.githubusercontent.com" in url.lower():
                        res = requests.get(url, headers=headers, timeout=12)
                        if res.status_code == 200: collected.extend(self.process_content(res.text, url))
                    else:
                        res = requests.get(url, headers=headers, timeout=12)
                        if res.status_code == 200:
                            soup = BeautifulSoup(res.text, 'html.parser')
                            for link in soup.find_all('a', class_='Link--primary'):
                                href = link.get('href', '')
                                if href.lower().endswith('.conf'):
                                    full_raw_url = quote("https://raw.githubusercontent.com" + href.replace('/blob/', '/'), safe=':/?=')
                                    r_res = requests.get(full_raw_url, headers=headers, timeout=10)
                                    if r_res.status_code == 200: collected.extend(self.process_content(r_res.text, full_raw_url))
                else:
                    res = requests.get(url, headers=headers, timeout=12)
                    if res.status_code == 200:
                        if url.endswith(('.txt', '.yaml')) or '://' in res.text[:200]: 
                            collected.extend(self.process_content(res.text, url))
                        else:
                            soup = BeautifulSoup(res.text, 'html.parser')
                            links = [urljoin(url, a['href'].strip()) for a in soup.find_all('a', href=True) 
                                     if any(k in a['href'].lower() for k in ['key=', 'sub', 'clash', '.txt', '.yaml', '.conf'])]
                            for sub_url in list(set(links))[:8]:
                                try:
                                    s_res = requests.get(sub_url, headers=headers, timeout=10)
                                    if s_res.status_code == 200: collected.extend(self.process_content(s_res.text, sub_url))
                                except: continue
                
                # Твой заветный счётчик проходов для Raw-источников
                if i % 50 == 0 or i == len(self.sources):
                    print(f"📊 [RAW Прогресс] Обработано URL-проходов: {i}/{len(self.sources)} | Найдено строк: {len(collected)}", flush=True)
            except: continue

        if collected:
            clean_list = sorted(list(set([l.strip() for l in collected if l.strip() and '://' in l])))
            
            # ТРОН (Все протоколы с разделением по файлам)
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

            # Программа Н (Страны без http/https/socks)
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

            print(f"🏁 [RAW ОБРАБОТКА] Сбор завершен успешно за {time.time() - start_time:.2f} сек!", flush=True)

if __name__ == "__main__":
    MainRawCollector().collect()
