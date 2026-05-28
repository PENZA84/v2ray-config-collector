import os
import re
import sys
import time
import concurrent.futures
from playwright.sync_api import sync_playwright

class ConfigFetcher:
    def __init__(self):
        # Строгое определение единых путей внутри v2ray_config_collector
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_path = os.path.join(self.base_dir, "data", "sources")
        
        os.makedirs(self.sources_path, exist_ok=True)
        
        self.main_sources = os.path.join(self.sources_path, "sources.txt")
        self.tg_sources = os.path.join(self.sources_path, "sources1.txt")
        
        self.timeout = 25000  # Таймаут в миллисекундах для Playwright (25 секунд)
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'

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
        """Интерактивное скачивание страницы: открытие в браузере и тотальный прожим всех кнопок"""
        # Если ссылка ведет на прямой текстовый raw-файл, открывать браузер нет смысла, качаем быстро
        if any(ext in url.lower() for ext in ['raw.githubusercontent', '.txt', '.yaml', '.json']):
            import requests
            try:
                res = requests.get(url, headers={'User-Agent': self.user_agent}, timeout=10)
                if res.status_code == 200:
                    return res.text
            except:
                pass
            return None

        # Для полноценных сайтов и блогов запускаем Ходока Playwright
        try:
            with sync_playwright() as p:
                # Запуск скрытого браузера Chromium
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1920, "height": 1080}
                )
                page = context.new_page()
                
                # Заходим на сайт напрямую
                page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                time.sleep(3)  # Базовая пауза для выполнения начальных скриптов сайта
                
                # --- ТОТАЛЬНЫЙ ПРОЖИМ КНОПОК И СХЛОПНУТЫХ БЛОКОВ ---
                # Селекторы для поиска кнопок раскрытия кода, спойлеров, кликалок Базы64
                selectors = [
                    "button", "input[type='button']", "input[type='submit']", 
                    "a.more-link", ".read-more", ".show-more", "[class*='btn']", 
                    "[class*='button']", "[id*='show']", "[class*='copy']", ".collapse"
                ]
                combined_selector = ", ".join(selectors)
                
                try:
                    buttons = page.query_selector_all(combined_selector)
                    if buttons:
                        for btn in buttons:
                            try:
                                if btn.is_visible() and btn.is_enabled():
                                    btn.click(timeout=1500)
                                    time.sleep(0.3)  # Микропауза между кликами
                            except:
                                continue
                        time.sleep(2)  # Даем время контенту полностью прогрузиться после кликов
                except:
                    pass

                # Забираем весь итоговый код страницы вместе со всеми раскрытыми данными
                final_html = page.content()
                browser.close()
                return final_html
        except Exception as e:
            # Если Playwright споткнулся на каком-то тяжелом сайте, пробуем забрать хоть какой-то текст через requests
            try:
                import requests
                res = requests.get(url, headers={'User-Agent': self.user_agent}, timeout=10)
                if res.status_code == 200:
                    return res.text
            except:
                pass
        return None

    def fetch_all(self):
        """ГЛАВНЫЙ ПРОЦЕСС: Многопоточное скачивание контента напрямую для коллекторов с прожимом кнопок"""
        sys.stdout.reconfigure(line_buffering=True)
        print("[INFO] [FETCHER] Запуск реактивного Граббера памяти с функциями Ходока...")
        
        # Проверка на пустоту стартовых баз
        if not os.path.exists(self.main_sources) or os.path.getsize(self.main_sources) == 0:
            print("[INFO] [FETCHER] Списки источников пусты, добавляю стартовый топ-набор...")
            self.sort_to_shelves([
                "https://raw.githubusercontent.com/freefq/free/master/v2",
                "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix"
            ])

        # Читаем ссылки Гитхаба и сайтов
        all_links = []
        if os.path.exists(self.main_sources):
            with open(self.main_sources, 'r', encoding='utf-8') as f:
                all_links = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not all_links:
            print("[WARN] [FETCHER] Ссылки для скачивания не найдены.")
            return []

        print(f"[INFO] [FETCHER] Качаю и прожимаю {len(all_links)} источников в 15 потоков через Playwright... 🚀")
        
        final_contents = []
        # Запуск параллельного движка (каждый поток создает свой изолированный инстанс браузера)
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(self.fetch_single_url, all_links)
            for res in results:
                if res:
                    final_contents.append(res)

        print(f"[INFO] [FETCHER] Успешно обработано и загружено контента: {len(final_contents)} шт. Чистота соблюдена! 💋")
        return final_contents

if __name__ == "__main__":
    ConfigFetcher().fetch_all()
