import os
import re
import sys
import time
import requests

class CountrySorter:
    def __init__(self):
        # Строгая привязка к твоей структуре папок Завода
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.base_dir, 'data', 'countries')
        self.strange_dir = os.path.join(self.output_dir, 'странные')
        
        # Регулярка для поиска кодов стран или IP-адресов для определения гео
        self.ip_pattern = re.compile(r'(?:\d{1,3}\.){3}\d{1,3}')
        
        # Список протоколов, которые мы ищем в файлах
        self.protocols = [
            'socks5', 'socks4', 'socks', 'http', 'https', 'ss', 'trojan', 
            'vmess', 'vless', 'tuic', 'hysteria', 'hysteria2', 'hy2'
        ]

    def get_ip_country(self, ip):
        """Определение страны по IP через бесплатный API (с защитой от зависаний)"""
        try:
            res = requests.get(f"https://ipapi.co/{ip}/country/", timeout=3)
            if res.status_code == 200 and len(res.text.strip()) == 2:
                return res.text.strip().upper()
        except:
            pass
        return 'UNKNOWN'

    def process_sorting(self):
        """Основной цикл сортировки прокси по странам с гвардейским фильтром файлов"""
        sys.stdout.reconfigure(line_buffering=True)
        
        if not os.path.exists(self.input_dir):
            print(f"⚠️ Папка с входными данными не найдена: {self.input_dir}", flush=True)
            return

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.strange_dir, exist_ok=True)

        print("🏭 Сортировщик Стран запускает гвардейский анализ баз...", flush=True)
        
        # Читаем файлы из папки уникальных
        files = os.listdir(self.input_dir)
        
        for file_name in files:
            # ГВАРДЕЙСКИЙ ЩИТ: Полностью игнорируем любые файлы-сборники!
            # Больше ни deduplicated.txt, ни ТГ deduplicated.txt сюда не пролезут!
            if 'deduplicated' in file_name.lower():
                print(f"🛡️ Сортировщик обошел стороной файл-сборник: {file_name}", flush=True)
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

                # Ищем IP адрес в строке конфигурации
                ip_match = self.ip_pattern.search(line)
                
                if ip_match:
                    ip = ip_match.group(0)
                    # Определяем страну
                    country = self.get_ip_country(ip)
                    
                    if country and country != 'UNKNOWN':
                        country_dir = os.path.join(self.output_dir, country)
                        os.makedirs(country_dir, exist_ok=True)
                        
                        # Сохраняем в папку конкретной страны
                        out_file = os.path.join(country_dir, file_name)
                        with open(out_file, 'a', encoding='utf-8') as out_f:
                            out_f.write(line + '\n')
                    else:
                        # Если страна не определилась — отправляем в странные
                        strange_file = os.path.join(self.strange_dir, file_name)
                        with open(strange_file, 'a', encoding='utf-8') as strange_f:
                            strange_f.write(line + '\n')
                else:
                    # Если в строке вообще нет IP (какой-то левый текст или битая ссылка) — в странные
                    strange_file = os.path.join(self.strange_dir, file_name)
                    with open(strange_file, 'a', encoding='utf-8') as strange_f:
                        strange_f.write(line + '\n')

        print("\n🏁 ========================================================", flush=True)
        print("✅ Сортировка по странам завершена! Все сборники deduplicated в безопасности.", flush=True)
        print("============================================================", flush=True)

if __name__ == "__main__":
    CountrySorter().process_sorting()
