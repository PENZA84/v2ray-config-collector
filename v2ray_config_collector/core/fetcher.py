import os
import sys
import time
import concurrent.futures
import requests
from playwright.sync_api import sync_playwright

class ConfigFetcher:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_path = os.path.join(self.base_dir, "data", "sources")
        os.makedirs(self.sources_path, exist_ok=True)
        
        self.main_sources = os.path.join(self.sources_path, "sources.txt")
        self.tg_sources = os.path.join(self.sources_path, "sources1.txt")
        
        self.timeout = 20000 
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'

    def sort_to_shelves(self, found_links_list):
        """Безопасная сортировка источников по файлам"""
        print("[INFO] [FETCHER] Сортировка ссылок-источников по полочкам...")
        
        def update_file(file_path, links):
            existing = set()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing = {line.strip() for line in f if line.strip()}
            
            new_links = [l for l in links if l not in existing]
            if new_links:
                with open(file_path, "a", encoding="utf-8") as f:
                    for link in new_links:
                        f.write(link + "\n")

        tg_links = [l.strip() for l in found_links_list if "t.me" in l or "telegram.me" in l]
        main_links = []
        for l in found_links_list:
            if l not in tg_links:
                if "github.com" in l and "/blob/" in l:
                    l = l.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                main_links.append(l)

        update_file(self.tg_sources, tg_links)
        update_file(self.main_sources, main_links)

    def fetch_single_url(self, url):
        """Интерактивное скачивание с защитой от зависаний"""
        # Сначала пробуем быстрый запрос
        try:
            res = requests.get(url, headers={'User-Agent': self.user_agent}, timeout=8)
            if res.status_code == 200 and len(res.text) > 100:
                # Если это явно конфиг-файл, возвращаем сразу
                if any(ext in url.lower() for ext in ['.txt', '.yaml', '.json', 'raw.github']):
                    return res.text
        except: pass

        # Запускаем ходока, если сайт сложный
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()
                page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                time.sleep(2)
                
                # Прожимаем кнопки
                selectors = ["button", ".btn", ".copy", ".show-more", "[class*='btn']"]
                for sel in selectors:
                    try:
                        page.click(sel, timeout=500)
                    except: continue
                
                content = page.content()
                browser.close()
                return content
        except Exception:
            return None

    def fetch_all(self):
        """Многопоточное скачивание с оптимизацией памяти"""
        sys.stdout.reconfigure(line_buffering=True)
        
        # Загрузка источников
        if not os.path.exists(self.main_sources):
            self.sort_to_shelves(["https://raw.githubusercontent.com/freefq/free/master/v2"])

        with open(self.main_sources, 'r', encoding='utf-8') as f:
            all_links = [l.strip() for l in f if l.strip() and not l.startswith('#')]

        print(f"[INFO] [FETCHER] Запуск граббера: {len(all_links)} источников...")
        
        # Снизили до 5 потоков для стабильности в GitHub Actions
        final_contents = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(self.fetch_single_url, all_links)
            for res in results:
                if res: final_contents.append(res)

        return final_contents

if __name__ == "__main__":
    ConfigFetcher().fetch_all()
