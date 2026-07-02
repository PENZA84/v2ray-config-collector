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
        # --- НАВИГАЦИЯ КОРНЕВЫХ ДИРЕКТОРИЙ ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        self.base_dir = current_dir
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                break
            self.base_dir = os.path.dirname(self.base_dir)

        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.base_dir, 'countries') 
        
        # 🛡️ ФИЛЬТР ПРОТОКОЛОВ: Исключаем только http/https. Socks4 и Socks5 разрешены
        self.bad_protocols = ('http://', 'https://')
        
        # Регулярное выражение для поиска ISO-кодов стран (две заглавные буквы)
        self.country_tag_pattern = re.compile(r'\b([A-Z]{2})\b')
        
        # Карта популярных доменных зон для локального определения
        self.domain_zone_map = {
            '.ru': 'RU', '.su': 'RU', '.ua': 'UA', '.by': 'BY', '.kz': 'KZ',
            '.us': 'US', '.uk': 'GB', '.de': 'DE', '.fr': 'FR', '.nl': 'NL',
            '.sg': 'SG', '.hk': 'HK', '.jp': 'JP', '.fi': 'FI', '.pl': 'PL'
        }

        # Панель статистики работы
        self.stats = {
            'total_processed': 0,
            'blocked_bad_protocols': 0, 
            'sorted_by_tags': 0,
            'sorted_by_zone': 0,
            'unknown_configs': 0,
            'saved_countries': set()
        }

    def extract_server_and_name(self, line):
        """Извлечение адреса сервера и имени конфигурации без внешних запросов"""
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
        """Определение страны по тегам в названии или доменной зоне"""
        if not host:
            return 'UNKNOWN'

        # 1. Проверка текстовых маркеров в имени прокси
        if name:
            matches = self.country_tag_pattern.findall(name)
            if matches:
                for match in matches:
                    if match != 'II' and match != 'TV': 
                        return match

        # 2. Проверка доменной зоны сервера
        host_lower = host.lower()
        for zone, country in self.domain_zone_map.items():
            if host_lower.endswith(zone):
                self.stats['sorted_by_zone'] += 1
                return country

        return 'UNKNOWN'

    def process_sorting(self):
        """Основной цикл распределения строк по плоской структуре стран"""
        sys.stdout.reconfigure(line_buffering=True)
        print("🏭 [ЦЕХ СОРТИРОВКИ] Запуск распределителя стран в плоские файлы countries/... 🚀", flush=True)
        
        if not os.path.exists(self.input_dir):
            print(f"⚠️ Папка с уникальными протоколами не найдена: {self.input_dir}", flush=True)
            return

        os.makedirs(self.output_dir, exist_ok=True)

        try:
            files = os.listdir(self.input_dir)
        except Exception as e:
            print(f"❌ Ошибка чтения директории {self.input_dir}: {e}", flush=True)
            return

        # Словарь для накопления строк: ключ — страна, значение — список строк
        country_buckets = defaultdict(list)

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
                
                if line.lower().startswith(self.bad_protocols):
                    self.stats['blocked_bad_protocols'] += 1
                    continue
                
                self.stats['total_processed'] += 1
                host, name = self.extract_server_and_name(line)
                
                country = self.detect_country_locally(host, name)
                country_buckets[country].append(line)
                
                if country != 'UNKNOWN':
                    self.stats['sorted_by_tags'] += 1
                    self.stats['saved_countries'].add(country)
                else:
                    self.stats['unknown_configs'] += 1

        # --- 👑 ПЛОСКАЯ НАРИЗАЦИЯ ФАЙЛОВ С ЛИМИТОМ В 85 МБ ---
        MAX_FILE_SIZE_BYTES = 85 * 1024 * 1024

        for country, lines_to_write in country_buckets.items():
            current_chunk_lines = []
            current_chunk_size = 0
            chunk_index = 0
            
            for line in lines_to_write:
                line_encoded = (line + "\n").encode('utf-8')
                line_len = len(line_encoded)
                
                # Если текущая строка превышает лимит в 85 МБ, сохраняем накопленный чанк
                if current_chunk_size + line_len > MAX_FILE_SIZE_BYTES and current_chunk_lines:
                    suffix = "" if chunk_index == 0 else str(chunk_index)
                    out_file = os.path.join(self.output_dir, f"{country}{suffix}.txt")
                    
                    with open(out_file, 'w', encoding='utf-8') as out_f:
                        out_f.write("".join(current_chunk_lines))
                    
                    current_chunk_lines = [line + "\n"]
                    current_chunk_size = line_len
                    chunk_index += 1
                else:
                    current_chunk_lines.append(line + "\n")
                    current_chunk_size += line_len
            
            # Сохранение финальной части или единственного файла
            if current_chunk_lines:
                suffix = "" if chunk_index == 0 else str(chunk_index)
                out_file = os.path.join(self.output_dir, f"{country}{suffix}.txt")
                with open(out_file, 'w', encoding='utf-8') as out_f:
                    out_f.write("".join(current_chunk_lines))

        print("\n📊 " + "="*24 + " ОТЧЁТ СОРТИРОВЩИКА СТРАН " + "="*24, flush=True)
        print(f"📦 ВСЕГО СТРОК ВЗЯТО В ОБРАБОТКУ: {self.stats['total_processed']} шт.", flush=True)
        print(f"🛡️ ЗАБЛОКИРОВАНО HTTP ПРОТОКОЛОВ: {self.stats['blocked_bad_protocols']} шт.", flush=True)
        print(f"🌍 РАСПРЕДЕЛЕНО ПО СТРАНАМ: {self.stats['sorted_by_tags']} шт.", flush=True)
        print(f"🗂️ ВСЕГО СФОРМИРОВАНО СТРАН В КОРНЕ: {len(self.stats['saved_countries'])} шт.", flush=True)
        print(f"👽 НЕОПРЕДЕЛЕННЫХ (UNKNOWN) НАПРАВЛЕНО: {self.stats['unknown_configs']} шт.", flush=True)
        print("-" * 88, flush=True)
        if self.stats['saved_countries']:
            print(f"✅ Результаты сохранены в корне папки countries: {', '.join(sorted(list(self.stats['saved_countries'])))}")
        print("========================================================================================\n", flush=True)

if __name__ == "__main__":
    CountrySorter().process_sorting()
