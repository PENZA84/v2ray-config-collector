import os
import re
import sys
import time
import json
import base64
import urllib.parse
from collections import defaultdict

class CountrySorter:
    def __init__(self):
        # --- МОНОЛИТНАЯ НАВИГАЦИЯ ЗАВОДА ЛЕИ ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        self.base_dir = current_dir
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                break
            self.base_dir = os.path.dirname(self.base_dir)

        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.base_dir, 'countries') # Исправлено на правильный корень по твоему указанию
        self.strange_dir = os.path.join(self.output_dir, 'STRANGE')
        
        # 🛡️ ЩИТ ДЛЯ ПРОГРАММЫ Н: Устаревшие протоколы, вызывающие слепые строки и ошибки подписки
        self.bad_protocols = ('http://', 'https://', 'socks://', 'socks4://', 'socks5://')
        
        # Регулярка для быстрого поиска ISO-кодов стран в именах (заглавные 2 буквы)
        self.country_tag_pattern = re.compile(r'\b([A-Z]{2})\b')
        
        # Наш внутренний словарь популярных буквенных зон для сверхзвукового анализа
        self.domain_zone_map = {
            '.ru': 'RU', '.su': 'RU', '.ua': 'UA', '.by': 'BY', '.kz': 'KZ',
            '.us': 'US', '.uk': 'GB', '.de': 'DE', '.fr': 'FR', '.nl': 'NL',
            '.sg': 'SG', '.hk': 'HK', '.jp': 'JP', '.fi': 'FI', '.pl': 'PL'
        }

        # Приборный щит аналитики
        self.stats = {
            'total_processed': 0,
            'blocked_bad_protocols': 0, # Счетчик отбитых плохих ссылок
            'sorted_by_tags': 0,
            'sorted_by_zone': 0,
            'strange_configs': 0,
            'saved_countries': set()
        }

    def extract_server_and_name(self, line):
        """Сверхскоростное извлечение адреса сервера и хэш-имени прокси без зависаний"""
        try:
            line = line.strip()
            if not line:
                return None, None
                
            name_part = ""
            if '#' in line:
                line, name_part = line.split('#', 1)
                name_part = urllib.parse.unquote(name_part).upper()

            if line.startswith('vmess://'):
                try:
                    b64_data = line[8:]
                    missing_padding = len(b64_data) % 4
                    if missing_padding:
                        b64_data += '=' * (4 - missing_padding)
                    dec = base64.b64decode(b64_data).decode('utf-8', errors='ignore')
                    data = json.loads(dec)
                    server = str(data.get('add', '')).strip()
                    ps_name = str(data.get('ps', '')).upper()
                    return server, (ps_name if ps_name else name_part)
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
                return host_port.strip('[]').strip(), name_part
                
            return None, name_part
        except:
            return None, None

    def detect_country_locally(self, host, name):
        """Линейный неуязвимый определитель стран БЕЗ внешних HTTP-запросов к API"""
        if not host:
            return 'UNKNOWN'

        # 1. Анализируем текстовые маркеры и флаги в названии прокси (самый точный метод!)
        if name:
            matches = self.country_tag_pattern.findall(name)
            if matches:
                for match in matches:
                    if match != 'II' and match != 'TV': 
                        return match

        # 2. Анализируем доменную зону сервера
        host_lower = host.lower()
        for zone, country in self.domain_zone_map.items():
            if host_lower.endswith(zone):
                self.stats['sorted_by_zone'] += 1
                return country

        return 'UNKNOWN'

    def process_sorting(self):
        """Генеральный цикл сортировки цеха по странам"""
        sys.stdout.reconfigure(line_buffering=True)
        print("🏭 [ЦЕХ СОРТИРОВКИ] Запуск неуязвимого распределителя sorter.py... 🚀", flush=True)
        
        if not os.path.exists(self.input_dir):
            print(f"⚠️ Папка с уникальными протоколами не найдена: {self.input_dir}", flush=True)
            return

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.strange_dir, exist_ok=True)

        try:
            files = os.listdir(self.input_dir)
        except Exception as e:
            print(f"❌ Ошибка чтения директории {self.input_dir}: {e}", flush=True)
            return

        country_buckets = defaultdict(lambda: defaultdict(list))
        strange_bucket = defaultdict(list)

        for file_name in files:
            if 'deduplicated' in file_name.lower() or file_name.startswith('chunk_'):
                continue
            if not file_name.endswith('.txt'):
                continue

            file_path = os.path.join(self.input_dir, file_name)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f if l.strip()]
            except Exception as e:
                print(f"❌ Ошибка чтения файла {file_name}: {e}", flush=True)
                continue

            for line in lines:
                if line.startswith('#'):
                    continue
                
                # --- 🛡️ БРОНЯ ДЛЯ ПРОГРАММЫ Н ---
                # Жестко отсекаем http, https и socks, чтобы не было пустых строк и ошибок подписок!
                if line.lower().startswith(self.bad_protocols):
                    self.stats['blocked_bad_protocols'] += 1
                    continue
                # --------------------------------
                
                self.stats['total_processed'] += 1
                host, name = self.extract_server_and_name(line)
                
                country = self.detect_country_locally(host, name)
                
                if country and country != 'UNKNOWN':
                    country_buckets[country][file_name].append(line)
                    self.stats['sorted_by_tags'] += 1
                    self.stats['saved_countries'].add(country)
                else:
                    strange_bucket[file_name].append(line)
                    self.stats['strange_configs'] += 1

        # --- ФИЗИЧЕСКАЯ ПАКЕТНАЯ ЗАПИСЬ НА ДИСК ---
        for country, file_data in country_buckets.items():
            country_path = os.path.join(self.output_dir, country)
            os.makedirs(country_path, exist_ok=True)
            
            for f_name, lines_to_write in file_data.items():
                out_file = os.path.join(country_path, f_name)
                with open(out_file, 'w', encoding='utf-8') as out_f:
                    out_f.write("\n".join(lines_to_write) + "\n")

        for f_name, lines_to_write in strange_bucket.items():
            strange_file = os.path.join(self.strange_dir, f_name)
            with open(strange_file, 'w', encoding='utf-8') as strange_f:
                strange_f.write("\n".join(lines_to_write) + "\n")

        print("\n📊 " + "="*24 + " ОТЧЁТ СВЕРХЗВУКОВОГО СОРТИРОВЩИКА СТРАН " + "="*24, flush=True)
        print(f"📦 ВСЕГО ЖИВЫХ СТРОК ВЗЯТО В ОБРАБОТКУ: {self.stats['total_processed']} шт.", flush=True)
        print(f"🛡️ ЗАБЛОКИРОВАНО УСТАРЕВШИХ (HTTP/SOCKS) ПРОТОКОЛОВ: {self.stats['blocked_bad_protocols']} шт. 🚫", flush=True)
        print(f"🌍 УСПЕШНО РАСПРЕДЕЛЕНО ПО СТРАНАМ: {self.stats['sorted_by_tags']} шт. 🔥", flush=True)
        print(f"🗂️ ВСЕГО СФОРМИРОВАНО НАЦИОНАЛЬНЫХ ПАПОК: {len(self.stats['saved_countries'])} шт.", flush=True)
        print(f"👽 СТРАННЫХ (НЕОПРЕДЕЛЕННЫХ) КОНФИГУРАЦИЙ ОСТАЛОСЬ: {self.stats['strange_configs']} шт.", flush=True)
        print(f"⏱️ СКОРОСТЬ СМЕНЫ: Выполнено мгновенно БЕЗ СЕТЕВЫХ ЗАВИСАНИЙ! 🛡️", flush=True)
        print("-" * 88, flush=True)
        if self.stats['saved_countries']:
            print(f"✅ Готовые локации на полочках: {', '.join(sorted(list(self.stats['saved_countries'])))} 🤍")
        print("========================================================================================\n", flush=True)

if __name__ == "__main__":
    CountrySorter().process_sorting()
