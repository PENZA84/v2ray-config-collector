import os
import requests

class ConfigFetcher:
    def __init__(self):
        # Базовые пути
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_path = os.path.join(self.base_dir, "data", "sources")
        self.raw_path = os.path.join(self.base_dir, "data", "raw")
        
        os.makedirs(self.sources_path, exist_ok=True)
        os.makedirs(self.raw_path, exist_ok=True)
        
        self.main_sources = os.path.join(self.sources_path, "sources.txt")
        self.tg_sources = os.path.join(self.sources_path, "sources1.txt")

    def sort_to_shelves(self, found_links_list):
        """Твоя логика сортировки ссылок по файлам"""
        print("🧼 Сортировка ссылок-источников...")
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
            if not link or link.startswith('#'): continue
            
            if "t.me" in link or "telegram.me" in link:
                if link not in existing_tg:
                    with open(self.tg_sources, "a", encoding="utf-8") as f:
                        f.write(link + "\n")
                    existing_tg.add(link)
            else:
                if "github.com" in link and "/blob/" in link:
                    link = link.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                if link not in existing_main:
                    with open(self.main_sources, "a", encoding="utf-8") as f:
                        f.write(link + "\n")
                    existing_main.add(link)

    def fetch_all(self):
        """ГЛАВНЫЙ ПРОЦЕСС: Скачивание контента из источников в data/raw"""
        print("📡 Запуск Граббера: Превращаем ссылки в файлы...")
        
        # Если списки источников пустые, давай добавим парочку базовых для старта
        if not os.path.exists(self.main_sources) or os.path.getsize(self.main_sources) == 0:
            print("💡 Списки пусты, добавляю стартовые наборы...")
            self.sort_to_shelves([
                "https://raw.githubusercontent.com/freefq/free/master/v2",
                "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix"
            ])

        # Читаем все ссылки из sources.txt (РАФ и сайты)
        all_links = []
        if os.path.exists(self.main_sources):
            with open(self.main_sources, 'r', encoding='utf-8') as f:
                all_links = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        # СКАЧИВАНИЕ
        count = 0
        for i, link in enumerate(all_links):
            try:
                print(f"📥 [{i+1}/{len(all_links)}] Качаю: {link}")
                res = requests.get(link, timeout=15)
                if res.status_code == 200:
                    file_name = f"raw_source_{i}.txt"
                    with open(os.path.join(self.raw_path, file_name), 'w', encoding='utf-8') as f:
                        f.write(res.text)
                    count += 1
            except Exception as e:
                print(f"⚠️ Ошибка на {link}: {e}")

        print(f"✅ Успешно скачано {count} файлов в data/raw! 💋")
