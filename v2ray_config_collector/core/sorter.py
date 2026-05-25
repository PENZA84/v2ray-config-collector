import os
import re
import socket
import requests
import shutil
import concurrent.futures
from urllib.parse import urlparse

class CountrySorter:
    def __init__(self):
        # Базовые пути Завода с учётом структуры твоего репозитория
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        
        # Финишная папка прямо в корне — для лёгкой интеграции с main.yml
        self.output_dir = os.path.join(self.base_dir, 'countries')
        
        # Список поддерживаемых протоколов, которые проходят досмотр
        self.protocols = [
            'vless', 'trojan', 'vmess', 'ss', 'socks5', 'socks4', 'socks', 
            'http', 'https', 'tuic', 'hysteria', 'hysteria2', 'hy2', 'ssh'
        ]
        
        self.timeout = 3

    def is_trash(self, link):
        """
        Таможенный контроль Леи: первичный досмотр всех прибывающих грузов.
        Полностью блокирует въезд пустышкам, огрызкам и нелегальному хламу любого протокола.
        """
        link = link.strip()
        # Если строка пустая, слишком короткая или обрывается на знаках сбоя (подходит для любого протокола)
        if len(link) < 15 or '://!' in link and (link.endswith('!') or link.endswith('!#')):
            return True
        return False

    def extract_host(self, link):
        """
        Папочкина ТАМОЖНЯ: тотальный обыск и потрошение любой ссылки.
        Вскрывает контрабанду во ВСЕХ протоколах (vless, vmess, trojan, ss, hy2), 
        вытряхивает двойные '@', уничтожает мусорные '!' и конфискует чистый хост!
        """
        try:
            # Отсекаем имя/комментарий в конце ссылки для любого протокола
            clean_link = link.split('#')[0]
            
            parsed = urlparse(clean_link)
            host = parsed.hostname
            
            # Если хитрая ссылка любого протокола с двойной '@' пытается запутать таможню
            if not host or '@' in parsed.netloc:
                # Таможня не обходит, а жёстко вскрывает строку после самой последней собаки '@'
                if '@' in clean_link:
                    remain = clean_link.split('@')[-1]
                else:
                    remain = clean_link.split('://')[-1]
                
                # Изымаем хост, отсекая порты, параметры "?" или пути "/"
                host = remain.split(':')[0].split('/')[0].split('?')[0]
                
            # Тотальная очистка конфискованного хоста от мусорных знаков '!' и '@' по краям
            if host:
                host = host.strip('!@:/\\ ')
                
            # Паспортный контроль хоста: проверяем наличие доменной точки или формата IP
            if host and ('.' in host or re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host)):
                return host
        except Exception:
            pass
        return None  # Контрабанда не прошла досмотр!

    def get_country_code(self, host):
        """Таможенный запрос: пробиваем ГЕО-прописку сервера через ip-api"""
        if not host: 
            return "unknown"
        try:
            # Если хост — домен, резолвим его в IP, чтобы база выдала 100% точный результат
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
        """Досмотр и сортировка одной строки на таможенном терминале"""
        if self.is_trash(link):
            return None  # Любой нелегал сразу депортируется в корзину
            
        host = self.extract_host(link)
        if not host:
            return None  # Если паспорт хоста поддельный — отбрасываем
            
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
        """Главный таможенный конвейер распределения для GitHub Actions"""
        print("[INFO] [ТАМОЖНЯ] Внимание! Таможня Завода приступает к тотальной чистке ВСЕХ протоколов...")
        if not os.path.exists(self.input_dir):
            print("[WARN] [ТАМОЖНЯ] Склады unique пусты! Нечего досматривать.")
            return

        # 1. Загружаем прибывшие грузы из файлов цеха unique
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
            print("[INFO] [ТАМОЖНЯ] Нет грузов для досмотра.")
            return

        print(f"[INFO] [ТАМОЖНЯ] Взято на обыск {len(all_links)} строк из всех протоколов. Включаем 15 потоков досмотра... 🚀")
        
        warehouse = {}

        # 2. Многопоточный обыск грязи во всех протоколах и распределение по странам
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(self.process_link, all_links)
            for res in results:
                if res:  # Сюда проходят только те, кто честно прошёл тотальный обыск
                    country = res['country']
                    proto = res['protocol']
                    link = res['link']
                    
                    if country not in warehouse:
                        warehouse[country] = {p: [] for p in self.protocols}
                        warehouse[country]['unknown'] = []
                        
                    warehouse[country][proto].append(link)

        # 3. Раскладка легального товара по складам-папкам в корне репозитория
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Полная зачистка старых складов перед новой выгрузкой
        for item in os.listdir(self.output_dir):
            item_path = os.path.join(self.output_dir, item)
            try:
                if os.path.isdir(item_path): shutil.rmtree(item_path)
                else: os.remove(item_path)
            except Exception: pass

        # Запись чистого, проверенного товара по папкам стран
        for country, protos_dict in warehouse.items():
            country_path = os.path.join(self.output_dir, country)
            os.makedirs(country_path, exist_ok=True)
            
            all_country_links = []
            
            # Распределяем по декларациям протоколов (vless.txt, trojan.txt...)
            for proto, links in protos_dict.items():
                if links:
                    sorted_links = sorted(links)
                    all_country_links.extend(sorted_links)
                    
                    with open(os.path.join(country_path, f"{proto}.txt"), 'w', encoding='utf-8') as f:
                        f.write("\n".join(sorted_links))
            
            # Контрабанда неопознанного вида — в unknown.txt
            if protos_dict['unknown']:
                sorted_unknown = sorted(protos_dict['unknown'])
                all_country_links.extend(sorted_unknown)
                with open(os.path.join(country_path, "unknown.txt"), 'w', encoding='utf-8') as f:
                    f.write("\n".join(sorted_unknown))
            
            # Финальный чистый пул для конкретной страны
            if all_country_links:
                with open(os.path.join(country_path, "all.txt"), 'w', encoding='utf-8') as f:
                    f.write("\n".join(sorted_all_country_links)))

        print(f"[INFO] [ТАМОЖНЯ] Успех! Гитхаб-контрабанда во всех протоколах разгромлена, чистые прокси на складах /countries/! 💋")

if __name__ == "__main__":
    CountrySorter().sort_now()
