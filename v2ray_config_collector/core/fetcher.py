import os
import requests
import concurrent.futures

class ConfigFetcher:
    def __init__(self):
        # Строгое определение единых путей внутри v2ray_config_collector
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_path = os.path.join(self.base_dir, "data", "sources")
        
        os.makedirs(self.sources_path, exist_ok=True)
        
        self.main_sources = os.path.join(self.sources_path, "sources.txt")
        self.tg_sources = os.path.join(self.sources_path, "sources1.txt")
        
        self.timeout = 10
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        }

    def sort_to_shelves(self, found_links_list):
        """Умное распределение новых найденных источников по файлам без дубликатов"""
        print("[INFO] [FETCHER] Сортировка ссылок-источников по полочкам...")
        
        existing_main = set()
        if os.path.exists(self.main_sources):
            with open(self.main_sources, 'r', encoding='utf-8') as f:
                existing_main = {line.strip() for line in f if line.strip()}
        
        existing_tg = set()
        if os.path.exists(self.tg_sources):
            with open(self.tg_sources, 'r', encoding='utf-8') as f:
                existing_tg = {line.strip() for line in f if line.strip()}

        for link in found_links_list:
            link = link.strip()
            if not link or link.startswith('#'): 
                continue
            
            # Если это Телеграм-канал или зеркало
            if "t.me" in link or "telegram.me" in link:
                if link not in existing_tg:
                    with open(self.tg_sources, "a", encoding="utf-8") as f:
                        f.write(link + "\n")
                    existing_tg.add(link)
            # Если это Гитхаб или обычный сайт
            else:
                if "github.com" in link and "/blob/" in link:
                    link = link.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                if link not in existing_main:
                    with open(self.main_sources, "a", encoding="utf-8") as f:
                        f.write(link + "\n")
                    existing_main.add(link)

    def fetch_single_url(self, url):
        """Быстрое скачивание одной ссылки в память"""
        try:
            res = requests.get(url, headers=self.headers, timeout=self.timeout)
            if res.status_code == 200:
                return res.text
        except:
            pass
        return None

    def fetch_all(self):
        """ГЛАВНЫЙ ПРОЦЕСС: Многопоточное скачивание контента напрямую для коллекторов"""
        print("[INFO] [FETCHER] Запуск реактивного Граббера памяти...")
        
        # Проверка на пустоту стартовых баз
        if not os.path.exists(self.main_sources) or os.path.getsize(self.main_sources) == 0:
            print("[INFO] [FETCHER] Списки источников пусты, добавляю стартовый топ-набор...")
            self.sort_to_shelves([
                "https://raw.githubusercontent.com/freefq/free/master/v2",
                "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix"
            ])

        # Читаем ссылки Гитхаба
        all_links = []
        if os.path.exists(self.main_sources):
            with open(self.main_sources, 'r', encoding='utf-8') as f:
                all_links = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not all_links:
            print("[WARN] [FETCHER] Ссылки для скачивания не найдены.")
            return []

        print(f"[INFO] [FETCHER] Качаю {len(all_links)} источников в 15 потоков... Поехали! 🚀")
        
        final_contents = []
        # Запуск параллельного движка
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(self.fetch_single_url, all_links)
            for res in results:
                if res:
                    final_contents.append(res)

        print(f"[INFO] [FETCHER] Успешно обработано и загружено контента: {len(final_contents)} шт. Чистота соблюдена! 💋")
        return final_contents

if __name__ == "__main__":
    ConfigFetcher().fetch_all()
