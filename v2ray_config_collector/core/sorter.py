import os
import re
import socket
import requests
import shutil
import concurrent.futures
from urllib.parse import urlparse

class CountrySorter:
    def __init__(self):
        # Базовые пути с учётом структуры репозитория
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        
        # Финишная папка прямо в корне — для лёгкой интеграции с main.yml
        self.output_dir = os.path.join(os.path.dirname(self.base_dir), 'countries')
        
        # Список поддерживаемых протоколов
        self.protocols = [
            'vless', 'trojan', 'vmess', 'ss', 'socks5', 'socks4', 'socks', 
            'http', 'https', 'tuic', 'hysteria', 'hysteria2', 'hy2', 'ssh'
        ]
        
        self.timeout = 3

    def is_trash(self, link):
        """Первичный досмотр прибывающих строк."""
        link = link.strip()
        if len(link) < 15 or '://!' in link and (link.endswith('!') or link.endswith('!#')):
            return True
        return False

    def extract_host(self, link):
        """Извлечение чистого хоста из ссылки любого протокола."""
        try:
            clean_link = link.split('#')[0]
            parsed = urlparse(clean_link)
            host = parsed.hostname
            
            if not host or '@' in parsed.netloc:
                if '@' in clean_link:
                    remain = clean_link.split('@')[-1]
                else:
                    remain = clean_link.split('://')[-1]
                
                host = remain.split(':')[0].split('/')[0].split('?')[0]
                
            if host:
                host = host.strip('!@:/\\ ')
                
            if host and ('.' in host or re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host)):
                return host
        except Exception:
            pass
        return None

    def get_country_code(self, host):
        """Проверка ГЕО-прописки сервера через ip-api."""
        if not host: 
            return "unknown"
        try:
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host):
                ip = socket.gethostbyname(host)
            else:
                ip = host
                
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=self.timeout).json()
            if res.get('status') == 'success':
                return res.get('countryCode').lower()
        except Exception:
            pass
        return "unknown"

    def process_link(self, link):
        """Досмотр и сортировка одной строки."""
        if self.is_trash(link):
            return None
            
        host = self.extract_host(link)
        if not host:
            return None
            
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
        """Главный конвейер распределения."""
        print("[INFO] Старт процесса очистки и сортировки всех протоколов...")
        if not os.path.exists(self.input_dir):
            print(f"[WARN] Папка {self.input_dir} не найдена! Нечего досматривать.")
            return

        all_links = []
        for filename in os.listdir(self.input_dir):
            if filename.endswith('.txt') and filename != 'dns_list.txt':
                file_path = os.path.join(self.input_dir, filename)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and '://' in line:
                            all_links.append(line)

        all_links = list(set(all_links))
        if not all_links:
            print("[INFO] Нет грузов для досмотра.")
            return

        print(f"[INFO] Взято на обработку {len(all_links)} строк. Запуск 15 потоков... 🚀")
        warehouse = {}

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

        os.makedirs(self.output_dir, exist_ok=True)
        
        # Очистка старых данных перед выгрузкой
        for item in os.listdir(self.output_dir):
            item_path = os.path.join(self.output_dir, item)
            try:
                if os.path.isdir(item_path): shutil.rmtree(item_path)
                else: os.remove(item_path)
            except Exception: pass

        # Запись товара по папкам стран
        for country, protos_dict in warehouse.items():
            country_path = os.path.join(self.output_dir, country)
            os.makedirs(country_path, exist_ok=True)
            
            all_country_links = []
            
            for proto, links in protos_dict.items():
                if links:
                    sorted_links = sorted(links)
                    all_country_links.extend(sorted_links)
                    
                    with open(os.path.join(country_path, f"{proto}.txt"), 'w', encoding='utf-8') as f:
                        f.write("\n".join(sorted_links))
            
            if protos_dict['unknown']:
                sorted_unknown = sorted(protos_dict['unknown'])
                all_country_links.extend(sorted_unknown)
                with open(os.path.join(country_path, "unknown.txt"), 'w', encoding='utf-8') as f:
                    f.write("\n".join(sorted_unknown))
            
            if all_country_links:
                with open(os.path.join(country_path, "all.txt"), 'w', encoding='utf-8') as f:
                    f.write("\n".join(sorted(all_country_links)))

        print("[INFO] Сортировка успешно завершена! Прокси разложены по папкам.")

if __name__ == "__main__":
    CountrySorter().sort_now()
