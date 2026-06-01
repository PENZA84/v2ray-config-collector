import os
import re
import sys
import time
import requests
import socket
import urllib.parse
import json
import base64

class CountrySorter:
    def __init__(self):
        # --- МОНОЛИТНАЯ НАВИГАЦИЯ (ЖЕСТКАЯ ПРИВЯЗКА) ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        self.base_dir = current_dir
        found_root = False
        # Ищем папку 'data' вверх по дереву (до 3 уровней)
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                found_root = True
                break
            self.base_dir = os.path.dirname(self.base_dir)
        
        if not found_root:
            self.base_dir = current_dir
        # ----------------------------------------

        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.base_dir, 'data', 'countries')
        self.strange_dir = os.path.join(self.output_dir, 'странные')
        
        print(f"DEBUG: Base directory: {self.base_dir}", file=sys.stderr)
        print(f"DEBUG: Input directory: {self.input_dir}", file=sys.stderr)
        print(f"DEBUG: Output directory: {self.output_dir}", file=sys.stderr)
        
        self.ip_pattern = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')
        self.geo_cache = {}
        self.dns_cache = {}

    def extract_server_address(self, line):
        try:
            line = line.strip()
            if not line:
                return None
                
            if line.startswith('vmess://'):
                try:
                    b64_data = line[8:].split('#')[0]
                    missing_padding = len(b64_data) % 4
                    if missing_padding:
                        b64_data += '=' * (4 - missing_padding)
                    dec = base64.b64decode(b64_data).decode('utf-8', errors='ignore')
                    data = json.loads(dec)
                    if data.get('add'):
                        return str(data['add']).strip()
                except:
                    pass
                    
            if '://' in line:
                clean_line = line.split('?')[0] if '?' in line else line
                parsed = urllib.parse.urlparse(clean_line)
                host_port = parsed.netloc
                if '@' in host_port:
                    host_port = host_port.split('@')[-1]
                if ':' in host_port:
                    host_port = host_port.split(':')[0]
                return host_port.strip('[]').strip()
                
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    return parts[0].strip()
            return None
        except Exception:
            return None

    def resolve_to_ip(self, host):
        if not host:
            return None
        if self.ip_pattern.match(host):
            return host
        if host in self.dns_cache:
            return self.dns_cache[host]
        try:
            ip = socket.gethostbyname(host)
            self.dns_cache[host] = ip
            return ip
        except Exception:
            self.dns_cache[host] = None
            return None

    def get_ip_country(self, ip):
        if not ip or ip == 'UNKNOWN':
            return 'UNKNOWN'
        if ip in self.geo_cache:
            return self.geo_cache[ip]
        try:
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=3)
            if res.status_code == 200:
                data = res.json()
                if data.get('status') == 'success' and data.get('countryCode'):
                    country = str(data['countryCode']).strip().upper()
                    if len(country) == 2:
                        self.geo_cache[ip] = country
                        return country
        except Exception:
            pass
        self.geo_cache[ip] = 'UNKNOWN'
        return 'UNKNOWN'

    def process_sorting(self):
        sys.stdout.reconfigure(line_buffering=True)
        
        if not os.path.exists(self.input_dir):
            print(f"⚠️ Папка с входными данными не найдена: {self.input_dir}", flush=True)
            return

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.strange_dir, exist_ok=True)

        print("🏭 Сортировщик Стран запускает гвардейский анализ баз...", flush=True)
        cleaned_outputs = set()

        try:
            files = os.listdir(self.input_dir)
        except Exception as e:
            print(f"❌ Ошибка чтения директории {self.input_dir}: {e}", flush=True)
            return
        
        for file_name in files:
            if 'deduplicated' in file_name.lower():
                print(f"🛡️ ЗАПРЕТ СРАБОТАЛ: Сортировщик обошел стороной базу дубликатов: {file_name}", flush=True)
                continue
            if not file_name.endswith('.txt'):
                continue

            file_path = os.path.join(self.input_dir, file_name)
            print(f"🔎 Обработка файла протокола: {file_name}...", flush=True)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"❌ Ошибка чтения файла {file_name}: {e}", flush=True)
                continue

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                host = self.extract_server_address(line)
                
                # Запросы к API делаем только если хост валидный, чтобы не тормозить поток
                if host:
                    ip = self.resolve_to_ip(host)
                    country = self.get_ip_country(ip) if ip else 'UNKNOWN'
                else:
                    country = 'UNKNOWN'
                
                if country and country != 'UNKNOWN':
                    country_dir = os.path.join(self.output_dir, country)
                    os.makedirs(country_dir, exist_ok=True)
                    out_file = os.path.join(country_dir, file_name)
                    
                    # Очищаем старый файл ТОЛЬКО ОДИН РАЗ при первой встрече в рамках этого запуска
                    if out_file not in cleaned_outputs:
                        if os.path.exists(out_file):
                            os.remove(out_file)
                        with open(out_file, 'w', encoding='utf-8') as f_init:
                            pass
                        cleaned_outputs.add(out_file)
                        
                    with open(out_file, 'a', encoding='utf-8') as out_f:
                        out_f.write(line + '\n')
                else:
                    strange_file = os.path.join(self.strange_dir, file_name)
                    
                    # Очищаем файл "странные" только один раз при первой записи
                    if strange_file not in cleaned_outputs:
                        if os.path.exists(strange_file):
                            os.remove(strange_file)
                        with open(strange_file, 'w', encoding='utf-8') as f_init:
                            pass
                        cleaned_outputs.add(strange_file)
                        
                    with open(strange_file, 'a', encoding='utf-8') as strange_f:
                        strange_f.write(line + '\n')
                
                # Пауза перенесена в логический блок запросов и уменьшена, 
                # чтобы скрипт не висел часами на тысячах строк
                if host and country == 'UNKNOWN':
                    time.sleep(0.05)

        print("\n🏁 ========================================================", flush=True)
        print("✅ Сортировка по странам завершена! Все сборники deduplicated в безопасности.", flush=True)
        print("============================================================", flush=True)

if __name__ == "__main__":
    CountrySorter().process_sorting()
