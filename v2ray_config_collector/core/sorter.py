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
        # Строгая привязка к структуре папок Завода
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.base_dir, 'data', 'countries')
        self.strange_dir = os.path.join(self.output_dir, 'странные')
        
        # Строгая регулярка для проверки, является ли строка чистым IPv4
        self.ip_pattern = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')
        
        # Кэш для IP и доменов, чтобы не долбить API повторно ради одинаковых серверов
        self.geo_cache = {}
        self.dns_cache = {}

    def extract_server_address(self, line):
        """ Безопасно вытаскивает адрес сервера (IP или домен) из готовых ссылок протоколов """
        try:
            line = line.strip()
            if not line:
                return None
                
            # Обработка VMESS (так как ссылка vmess:// полностью зашита в base64)
            if line.startswith('vmess://'):
                try:
                    b64_data = line[8:].split('#')[0]
                    # Добавляем паддинг, если длина не кратна 4
                    missing_padding = len(b64_data) % 4
                    if missing_padding:
                        b64_data += '=' * (4 - missing_padding)
                    dec = base64.b64decode(b64_data).decode('utf-8', errors='ignore')
                    data = json.loads(dec)
                    if data.get('add'):
                        return str(data['add']).strip()
                except:
                    pass
                    
            # Обработка остальных текстовых URL-ссылок (vless://, trojan://, ss://, hysteria2:// и т.д.)
            if '://' in line:
                # Предварительно отсекаем параметры конфигурации, чтобы не сбивать urlparse
                clean_line = line.split('?')[0] if '?' in line else line
                parsed = urllib.parse.urlparse(clean_line)
                host_port = parsed.netloc
                
                # Если в netloc есть авторизация (user:pass@host:port)
                if '@' in host_port:
                    host_port = host_port.split('@')[-1]
                # Отсекаем порт, если он указан через двоеточие
                if ':' in host_port:
                    host_port = host_port.split(':')[0]
                # Убираем квадратные скобки (бывают у IPv6), оставляя чистый хост
                return host_port.strip('[]').strip()
                
            # Если в файле вдруг оказалась обычная строка вида host:port
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    return parts[0].strip()
                    
            return None
        except Exception:
            return None

    def resolve_to_ip(self, host):
        """ Превращает доменное имя в IP адрес с кэшированием """
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
        """ Определение страны по IP через быстрый и надежный ip-api.com с кэшем """
        if not ip or ip == 'UNKNOWN':
            return 'UNKNOWN'
            
        if ip in self.geo_cache:
            return self.geo_cache[ip]
            
        try:
            # Переключено на стабильный ip-api.com, возвращающий ISO-коды стран без жестких лимитов зависания
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=4)
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
        """ Основной цикл сортировки прокси по странам с гвардейским фильтром файлов """
        sys.stdout.reconfigure(line_buffering=True)
        
        if not os.path.exists(self.input_dir):
            print(f"⚠️ Папка с входными данными не найдена: {self.input_dir}", flush=True)
            return

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.strange_dir, exist_ok=True)

        print("🏭 Сортировщик Стран запускает гвардейский анализ баз...", flush=True)
        
        # Множество для отслеживания очищенных файлов вынесено наверх, 
        # чтобы файлы не затирались повторно при обработке строк!
        cleaned_outputs = set()

        try:
            files = os.listdir(self.input_dir)
        except Exception as e:
            print(f"❌ Ошибка чтения директории {self.input_dir}: {e}", flush=True)
            return
        
        for file_name in files:
            # 🛡️ ЖЕЛЕЗОБЕТОННЫЙ ГВАРДЕЙСКИЙ ЗАПРЕТ:
            # Полностью игнорируем чтение любых файлов, содержащих 'deduplicated' (хоть .json, хоть .txt)
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

                # 1. Извлекаем хост (домен или IP) из готовой ссылки
                host = self.extract_server_address(line)
                
                # 2. Превращаем домен в IP (если сервер указан буквами)
                ip = self.resolve_to_ip(host) if host else None
                
                # 3. Определяем гео-позицию через API
                country = self.get_ip_country(ip) if ip else 'UNKNOWN'
                
                if country and country != 'UNKNOWN':
                    country_dir = os.path.join(self.output_dir, country)
                    os.makedirs(country_dir, exist_ok=True)
                    out_file = os.path.join(country_dir, file_name)
                    
                    # Если файл открываем первый раз за запуск — очищаем его от старых записей
                    if out_file not in cleaned_outputs:
                        if os.path.exists(out_file):
                            os.remove(out_file)
                        # Создаем пустой файл и фиксируем его в очищенных
                        with open(out_file, 'w', encoding='utf-8') as f_init:
                            pass
                        cleaned_outputs.add(out_file)
                        
                    with open(out_file, 'a', encoding='utf-8') as out_f:
                        out_f.write(line + '\n')
                else:
                    # Если адрес не распознан, DNS упал или API выдал ошибку — пишем в "странные"
                    strange_file = os.path.join(self.strange_dir, file_name)
                    
                    if strange_file not in cleaned_outputs:
                        if os.path.exists(strange_file):
                            os.remove(strange_file)
                        with open(strange_file, 'w', encoding='utf-8') as f_init:
                            pass
                        cleaned_outputs.add(strange_file)
                        
                    with open(strange_file, 'a', encoding='utf-8') as strange_f:
                        strange_f.write(line + '\n')
                        
                # Небольшой таймаут для защиты API от бана, если это новый IP
                if host and host not in self.geo_cache:
                    time.sleep(0.3)

        print("\n🏁 ========================================================", flush=True)
        print("✅ Сортировка по странам завершена! Все сборники deduplicated в безопасности.", flush=True)
        print("============================================================", flush=True)

if __name__ == "__main__":
    CountrySorter().process_sorting()
