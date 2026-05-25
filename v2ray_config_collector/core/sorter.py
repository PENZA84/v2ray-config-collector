import os
import re
import socket
import requests
import shutil
import concurrent.futures
from urllib.parse import urlparse

class CountrySorter:
    def __init__(self):
        # Привязка к нашей экосистеме Завода
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        
        # Строгое, красивое и правильное название финальной папки на Заводе!
        self.output_dir = os.path.join(self.base_dir, 'countries')
        
        # Список поддерживаемых протоколов для создания файлов внутри стран
        self.protocols = [
            'vless', 'trojan', 'vmess', 'ss', 'socks5', 'socks4', 'socks', 
            'http', 'https', 'tuic', 'hysteria', 'hysteria2', 'hy2', 'ssh'
        ]
        
        self.timeout = 3

    def extract_host(self, link):
        """Ювелирное извлечение IP-адреса или домена из прокси-ссылки"""
        try:
            parsed = urlparse(link)
            host = parsed.hostname
            if not host and '@' in parsed.netloc:
                host = parsed.netloc.split('@')[-1].split(':')[0]
            if not host:
                match = re.search(r'@([^:/\s]+)', link)
                if match: host = match.group(1)
            return host
        except:
            return None

    def get_country_code(self, host):
        """Определяет двухбуквенный ISO-код страны (us, de, sg) для названий папок"""
        if not host: 
            return "unknown"
        try:
            # Если хост — домен, быстро резолвим его в IP для стабильности API
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host):
                ip = socket.gethostbyname(host)
            else:
                ip = host
                
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=self.timeout).json()
            if res.get('status') == 'success':
                # Код страны в нижнем регистре (например, 'us', 'de', 'vn'), как на твоем скриншоте 1236
                return res.get('countryCode').lower()
        except:
            pass
        return "unknown"

    def process_link(self, link):
        """Анализ ссылки: определение её протокола и короткого кода страны"""
        host = self.extract_host(link)
        country_code = self.get_country_code(host)
        
        proto_found = 'unknown'
        for proto in self.protocols:
            if link.lower().startswith(f"{proto}://"):
                proto_found = proto
                break
                
        return {
            'link': link,
            'country': country_code,
            'protocol': proto_found
        }

    def sort_now(self):
        """Главный конвейер: считывает unique и создаёт папочную структуру а-ля Гитхаб"""
        print("[INFO] [SORTER] Запуск разделки базы по странам...")
        if not os.path.exists(self.input_dir):
            print("[WARN] [SORTER] Папка unique пуста! Нам нечего разделять.")
            return

        # 1. Читаем все чистые прокси из памяти unique
        all_links = []
        for filename in os.listdir(self.input_dir):
            if filename.endswith('.txt') and filename != 'dns_list.txt':
                with open(os.path.join(self.input_dir, filename), 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '://' in line:
                            all_links.append(line)

        all_links = list(set(all_links))
        if not all_links:
            print("[INFO] [SORTER] Нет прокси-ссылок для распределения.")
            return

        print(f"[INFO] [SORTER] Найдено {len(all_links)} уникальных узлов. Запуск 15 потоков гео-анализа... 🚀")
        
        # Временный склад структуры: { 'us': { 'vless': [], 'trojan': [] } }
        warehouse = {}

        # 2. Многопоточный запуск пробива стран
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(self.process_link, all_links)
            for res in results:
                if res:
                    country = res['country']
                    proto = res['protocol']
                    link = res['link']
                    
                    if country not in warehouse:
                        warehouse[country] = {p: [] for p in self.protocols}
                        warehouse[country]['unknown'] = []
                        
                    warehouse[country][proto].append(link)

        # 3. Генерация структуры на диске в главной папке countries
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Полностью очищаем папку countries перед заливкой новой свежей разделки
        for item in os.listdir(self.output_dir):
            item_path = os.path.join(self.output_dir, item)
            try:
                if os.path.isdir(item_path): shutil.rmtree(item_path)
                else: os.remove(item_path)
            except: pass

        # Записываем папки и файлы строго по твоему закону Гитхаба (Скрины 1236, 1237)
        for country, protos_dict in warehouse.items():
            # Создаем короткую папку страны (countries/us/, countries/de/, countries/vn/)
            country_path = os.path.join(self.output_dir, country)
            os.makedirs(country_path, exist_ok=True)
            
            all_country_links = []
            
            # Записываем раздельные файлы протоколов внутри папки страны
            for proto, links in protos_dict.items():
                if links:
                    sorted_links = sorted(links)
                    all_country_links.extend(sorted_links)
                    
                    # Запись конкретного протокола (например, vless.txt)
                    file_name = f"{proto}.txt"
                    with open(os.path.join(country_path, file_name), 'w', encoding='utf-8') as f:
                        f.write("\n".join(sorted_links))
            
            # Если нашлись неопознанные протоколы, пишем их в unknown.txt, как на скрине 1237!
            if protos_dict['unknown']:
                sorted_unknown = sorted(protos_dict['unknown'])
                all_country_links.extend(sorted_unknown)
                with open(os.path.join(country_path, "unknown.txt"), 'w', encoding='utf-8') as f:
                    f.write("\n".join(sorted_unknown))
            
            # Создаем тот самый файл all.txt, объединяющий всё добро этой страны
            if all_country_links:
                with open(os.path.join(country_path, "all.txt"), 'w', encoding='utf-8') as f:
                    f.write("\n".join(sorted(all_country_links)))

        print(f"[INFO] [SORTER] Ура! База разделена на {len(warehouse)} стран и разложена по папкам в /countries/! 💋")

if __name__ == "__main__":
    CountrySorter().sort_now()
