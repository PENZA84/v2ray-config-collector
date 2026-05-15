import os
import re

class ConfigFetcher:
    def __init__(self):
        # Оставляем твои пути, мой дорогой
        self.base_data_path = "v2ray_config_collector/data/sources"
        os.makedirs(self.base_data_path, exist_ok=True)
        self.main_sources = os.path.join(self.base_data_path, "sources.txt")
        self.tg_sources = os.path.join(self.base_data_path, "sources1.txt")

    def sort_to_shelves(self, found_links_list):
        """Твоя логика сортировки по полочкам"""
        print("🧼 Завод PENZA84: Начинаю сортировку найденных сокровищ...")
        
        # Читаем существующие, чтобы не было дублей
        existing_main = set()
        if os.path.exists(self.main_sources):
            with open(self.main_sources, 'r', encoding='utf-8') as f: 
                existing_main = set(line.strip() for line in f)
                
        existing_tg = set()
        if os.path.exists(self.tg_sources):
            with open(self.tg_sources, 'r', encoding='utf-8') as f: 
                existing_tg = set(line.strip() for line in f)

        new_tg_count = 0
        new_main_count = 0

        for link in found_links_list:
            link = link.strip()
            if not link or link.startswith('#'): continue

            # 1. ПОЛОЧКА ТЕЛЕГРАМА
            if "t.me" in link or "telegram.me" in link:
                if link not in existing_tg:
                    with open(self.tg_sources, "a", encoding="utf-8") as f:
                        f.write(link + "\n")
                    existing_tg.add(link)
                    new_tg_count += 1
                    
            # 2. ПОЛОЧКА RAW И САЙТОВ
            else:
                if "github.com" in link and "/blob/" in link:
                    link = link.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                
                if link not in existing_main:
                    with open(self.main_sources, "a", encoding="utf-8") as f:
                        f.write(link + "\n")
                    existing_main.add(link)
                    new_main_count += 1

        print(f"✅ Сортировка окончена, мой дорогой!")
        print(f"📥 В sources1.txt (Telegram) добавлено: {new_tg_count}")
        print(f"📥 В sources.txt (RAW/Сайты) добавлено: {new_main_count} 💋")

    def fetch_all(self):
        """Этот метод вызывает Завод (main.py)"""
        # Сюда можно добавить код, который СНАЧАЛА находит ссылки (например, парсит README)
        # А пока просто заглушка для примера, чтобы Завод не ругался
        print("📡 Запуск Граббера ссылок...")
        
        # Пример: если у тебя есть список ссылок для сортировки, передай его сюда
        # Если ссылок пока нет, он просто отчитается о готовности
        test_links = [] 
        self.sort_to_shelves(test_links)
