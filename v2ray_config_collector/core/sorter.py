import os
import re
import socket
import requests
from urllib.parse import urlparse

class CountrySorter:
    def __init__(self):
        # Базовые пути Завода
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.base_dir, 'data', 'countries')
        
        # Твой строгий порядок протоколов внутри файла страны
        self.protocols_order = [
            'vless', 'trojan', 'vmess', 'ss', 'socks5', 'socks4', 'socks', 
            'http', 'https', 'tuic', 'hysteria', 'hysteria2', 'hy2', 'ssh'
        ]
        
        # Русские имена для красивых файлов
        self.country_names = {
            'DE': 'Германия', 'US': 'США', 'NL': 'Нидерланды', 'FI': 'Финляндия',
            'FR': 'Франция', 'GB': 'Великобритания', 'PL': 'Польша', 'SE': 'Швеция',
            'TR': 'Турция', 'HK': 'Гонконг', 'SG': 'Сингапур', 'JP': 'Япония',
            'RU': 'Россия', 'UA': 'Украина', 'KZ': 'Казахстан'
        }

    def extract_host(self, link):
        """Вытаскивает IP или домен из ссылки"""
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

    def get_country(self, host):
        """Определяет страну по хосту"""
        if not host: return "Неизвестно"
        try:
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host):
                ip = socket.gethostbyname(host)
            else:
                ip = host
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=3).json()
            if res.get('status') == 'success':
                code = res.get('countryCode')
                return self.country_names.get(code, f"Страна_{code}")
        except:
            pass
        return "Неизвестно"

    def sort_now(self):
        """Берет проверенное из unique и раскладывает по странам блоками"""
        print("[INFO] [SORTER] Запуск разделки базы по странам...")
        if not os.path.exists(self.input_dir):
            print("[WARN] Папка unique пуста.")
            return

        # Собираем всё проверенное сырье
        all_links = []
        for filename in os.listdir(self.input_dir):
            if filename.endswith('.txt'):
                with open(os.path.join(self.input_dir, filename), 'r', encoding='utf-8') as f:
                    all_links.extend([line.strip() for line in f if line.strip() and '://' in line])

        all_links = list(set(all_links))
        if not all_links:
            print("[INFO] Нет ссылок для сортировки.")
            return

        # Склад для сортировки: { 'Германия': { 'vless': [], 'trojan': [] } }
        warehouse = {}

        print(f"[INFO] [SORTER] Сортируем {len(all_links)} прокси...")
        for link in all_links:
            host = self.extract_host(link)
            country = self.get_country(host)
            
            proto_found = 'other'
            for proto in self.protocols_order:
                if link.lower().startswith(f"{proto}://"):
                    proto_found = proto
                    break
            
            if country not in warehouse:
                warehouse[country] = {p: [] for p in self.protocols_order}
                warehouse[country]['other'] = []
                
            warehouse[country][proto_found].append(link)

        # Запись файлов стран
        os.makedirs(self.output_dir, exist_ok=True)
        # Очищаем старую разделку
        for f in os.listdir(self.output_dir):
            if f.endswith('.txt'): os.remove(os.path.join(self.output_dir, f))

        for country, protos in warehouse.items():
            country_lines = []
            # Собираем строго по твоему порядку протоколов!
            for proto in self.protocols_order:
                if protos[proto]:
                    country_lines.extend(sorted(protos[proto]))
            if protos['other']:
                country_lines.extend(sorted(protos['other']))

            if country_lines:
                with open(os.path.join(self.output_dir, f"{country}.txt"), 'w', encoding='utf-8') as f:
                    f.write("\n".join(country_lines))

        print(f"[INFO] [SORTER] Разделка завершена! Все файлы стран лежат в /data/countries/ ✨")

if __name__ == "__main__":
    CountrySorter().sort_now()
