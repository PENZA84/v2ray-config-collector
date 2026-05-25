import os
import re
import requests
import yaml
import json
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode

class MainRawCollector:
    def __init__(self):
        # Базовые пути и настройки проекта
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources.txt')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.max_file_size_mb = 40
        
        # Единый глобальный список поддерживаемых протоколов
        self.protocols = [
            'naive+https', 'shadowtls', 'trusttunnel', 'hysteria2', 'wireguard', 
            'juicity', 'socks5', 'socks4', 'anytls', 'vmess', 'vless', 'trojan', 
            'naive', 'socks', 'https', 'http', 'tuic', 'hy2', 'ssh', 'wg', 'ss'
        ]
        
        # Оптимизированная компиляция регулярного выражения
        proto_pattern = '|'.join([re.escape(p) for p in self.protocols])
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')
        
        self.sources = self.load_sources()

    def load_sources(self):
        """Загрузка источников из файла конфигурации"""
        if not os.path.exists(self.sources_file): 
            return []
        links = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('http'): 
                    links.append(line)
        return links

    def parse_clash_yaml(self, yaml_text):
        """Продвинутый парсер Clash YAML с поддержкой Reality, gRPC, WS и SNI"""
        extracted = []
        try:
            data = yaml.safe_load(yaml_text)
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
                    uuid = p.get('uuid') or p.get('password')
                    
                    if not server or not port: 
                        continue
                    
                    # Сбор дополнительных параметров для сложных протоколов (Reality, WS, gRPC)
                    params = {}
                    if p.get('network'): 
                        params['type'] = p.get('network')
                    if p.get('tls'): 
                        params['security'] = 'tls'
                    if p.get('servername'): 
                        params['sni'] = p.get('servername')
                    if p.get('ws-opts') and isinstance(p['ws-opts'], dict):
                        ws_path = p['ws-opts'].get('path')
                        if ws_path: 
                            params['path'] = ws_path
                    if p.get('grpc-opts') and isinstance(p['grpc-opts'], dict):
                        grpc_name = p['grpc-opts'].get('grpc-service-name')
                        if grpc_name: 
                            params['serviceName'] = grpc_name

                    param_str = f"?{urlencode(params)}" if params else ""

                    if p_type == 'vless':
                        extracted.append(f"vless://{uuid}@{server}:{port}{param_str}#{name}")
                        
                    elif p_type == 'vmess':
                        v_json = {
                            "v": "2", "ps": name, "add": str(server), "port": str(port), 
                            "id": str(uuid), "aid": "0", "net": p.get('network', 'tcp'), 
                            "type": "none", "host": p.get('servername', ''), 
                            "path": p.get('ws-opts', {}).get('path', '') if isinstance(p.get('ws-opts'), dict) else '', 
                            "tls": "tls" if p.get('tls') else ""
                        }
                        encoded = base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')
                        extracted.append(f"vmess://{encoded}")
                        
                    elif p_type == 'trojan':
                        extracted.append(f"trojan://{uuid}@{server}:{port}{param_str}#{name}")
                        
                    elif p_type == 'ss':
                        cipher = p.get('cipher', 'aes-256-gcm')
                        user_info = base64.b64encode(f"{cipher}:{uuid}".encode('utf-8')).decode('utf-8')
                        extracted.append(f"ss://{user_info}@{server}:{port}#{name}")
                        
                    elif p_type in self.protocols or f"{p_type}" in ['hy2']:
                        proto_name = 'hysteria2' if p_type == 'hy2' else p_type
                        extracted.append(f"{proto_name}://{uuid}@{server}:{port}#{name}")
                except Exception: 
                    continue
        except Exception: 
            pass
        return extracted

    def process_content(self, text):
        """Парсинг контента: определение типа (Clash YAML или сырой текст)"""
        if 'proxies:' in text: 
            return self.parse_clash_yaml(text)
        
        found = self.regex_pattern.findall(text)
        clean_found = []
        
        for link in found:
            link = link.strip().rstrip('.')
            # Исключение мусорных строк и технических заголовков
            if any(bad in link for bad in ['User-Agent', 'headers', 'Pragma', 'cache-control', 'Host,']):
                continue
            clean_found.append(link)
            
        return clean_found

    def split_and_save_file(self, prefix, base_name, lines):
        """Разделение на чанки по 40МБ и сохранение результатов"""
        if not lines: 
            return  
        full_base_name = f"{prefix}{base_name}"
        
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f == f"{full_base_name}.txt" or re.match(r'^' + re.escape(full_base_name) + r'\s+\d+\.txt$', f):
                    try: 
                        os.remove(os.path.join(self.output_dir, f))
                    except: 
                        pass

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
        """Основной цикл сбора конфигураций со всех апстримов"""
        if not self.sources: 
            return
        collected = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        }
        
        for url in self.sources:
            try:
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200: 
                    continue
                content = res.text
                
                if url.endswith('.txt') or url.endswith('.yaml') or '://' in content[:200]:
                    collected.extend(self.process_content(content))
                    continue
                
                # Поиск скрытых подписок на веб-страницах (до 8 ссылок второго уровня)
                soup = BeautifulSoup(content, 'html.parser')
                links = [urljoin(url, a['href'].strip()) for a in soup.find_all('a', href=True) if any(k in a['href'].lower() for k in ['key=', 'sub', 'clash', '.txt', '.yaml'])]
                
                for sub_url in list(set(links))[:8]:
                    try:
                        s_res = requests.get(sub_url, headers=headers, timeout=10)
                        if s_res.status_code == 200: 
                            collected.extend(self.process_content(s_res.text))
                    except: 
                        continue
            except: 
                continue

        if collected:
            # Дедупликация и фиксация
            clean = list(set([l.strip() for l in collected if l.strip() and '://' in l]))
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Сохранение общего файла deduplicated.txt
            self.split_and_save_file('', 'deduplicated', clean)
            
            # Сохранение по отдельным протоколам
            for proto in self.protocols:
                proto_lines = [l for l in clean if l.lower().startswith(f"{proto}://")]
                if proto_lines:
                    self.split_and_save_file('', proto, proto_lines)

if __name__ == "__main__":
    MainRawCollector().collect()
