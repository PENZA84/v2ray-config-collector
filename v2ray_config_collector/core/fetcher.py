import os
import sys
import time
import concurrent.futures
import requests
from playwright.sync_api import sync_playwright

class ConfigFetcher:
    def __init__(self):
        # --- ENGLISH PRODUCTION ENVIRONMENT NAVIGATION ---
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_path = os.path.join(self.base_dir, "data", "sources")
        os.makedirs(self.sources_path, exist_ok=True)
        
        self.main_sources = os.path.join(self.sources_path, "sources.txt")
        self.tg_sources = os.path.join(self.sources_path, "sources1.txt")
        
        self.timeout = 20000 
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        # Наша заводская статистика
        self.stats = {
            'total_processed': 0,
            'fast_requests_success': 0,
            'playwright_success': 0,
            'failed_links': 0
        }

    def sort_to_shelves(self, found_links_list):
        """Безопасная и точная сортировка источников по полочкам Трона"""
        print("🗂️ [FETCHER] Сортировка ссылок-источников по целевым контейнерам...", flush=True)
        
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

    def fetch_with_browser(self, browser, url):
        """Безопасный изолированный вызов браузера внутри единого движка"""
        try:
            context = browser.new_context(user_agent=self.user_agent)
            page = context.new_page()
            page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            time.sleep(1.5)
            
            # Прожимаем коварные кнопки скрытия данных на страницах
            selectors = ["button", ".btn", ".copy", ".show-more", "[class*='btn']"]
            for sel in selectors:
                try:
                    page.click(sel, timeout=300)
                except: 
                    continue
            
            content = page.content()
            context.close()
            if content and len(content) > 100:
                self.stats['playwright_success'] += 1
                return content
        except:
            pass
        return None

    def fetch_all(self):
        """Многопоточный гибридный конвейер выкачки с оптимизацией памяти"""
        sys.stdout.reconfigure(line_buffering=True)
        
        print("🏭 [ГЕНЕРАЛЬНЫЙ ГРАББЕР] Включение Цеха Снабжения Завода... 🤍🌪️🚀", flush=True)
        
        # Первичный запуск — если файла нет, подкидываем стартовый проверенный лист
        if not os.path.exists(self.main_sources):
            self.sort_to_shelves(["https://raw.githubusercontent.com/freefq/free/master/v2"])

        with open(self.main_sources, 'r', encoding='utf-8') as f:
            all_links = [l.strip() for l in f if l.strip() and not l.startswith('#')]

        if not all_links:
            print("ℹ️ Список внешних источников пуст, мой капитан.", flush=True)
            return []

        print(f"📥 Загружено сырьевых адресов из sources.txt: {len(all_links)} шт.", flush=True)
        print("⚡ Запуск гибридного реактора (Requests + Оптимизированный Playwright)...", flush=True)
        
        start_time = time.time()
        final_contents = []
        links_for_browser = []

        # ШАГ 1: Быстрый прострел через сверхскоростные requests (для RAW-листов и гитхаба)
        for url in all_links:
            self.stats['total_processed'] += 1
            if any(ext in url.lower() for ext in ['.txt', '.yaml', '.json', 'raw.github']):
                try:
                    res = requests.get(url, headers={'User-Agent': self.user_agent}, timeout=6)
                    if res.status_code == 200 and len(res.text) > 100:
                        final_contents.append(res.text)
                        self.stats['fast_requests_success'] += 1
                        continue
                except:
                    pass
            # Если это сложный динамический веб-сайт — отправляем его на обработку браузеру
            links_for_browser.append(url)

        # ШАГ 2: Безопасная выкачка веб-сайтов через ЕДИНЫЙ запущенный браузер Playwright
        if links_for_browser:
            print(f"🤖 Передаем {len(links_for_browser)} сложных сайтов на рендеринг движку Playwright...", flush=True)
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    
                    # Запускаем стабильный пул на 3 параллельных воркера для браузера
                    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                        futures = {executor.submit(self.fetch_with_browser, browser, url): url for url in links_for_browser}
                        for future in concurrent.futures.as_completed(futures):
                            res = future.result()
                            if res:
                                final_contents.append(res)
                            else:
                                self.stats['failed_links'] += 1
                                
                    browser.close()
            except Exception as e:
                print(f"⚠️ Сбой движка автоматизации: {e}", flush=True)

        elapsed = time.time() - start_time
        speed_pages = len(all_links) / elapsed if elapsed > 0 else 0

        # Наш потрясающий, красивейший приборный отчет! 📊🦖
        print("\n📊 " + "-"*20 + " ОТЧЁТ СКОРОСТИ ЦЕХА СНАБЖЕНИЯ " + "-"*20, flush=True)
        print(f"📦 ВСЕГО ССЫЛОК ОБРАБОТАНО НА КОНВЕЙЕРЕ: {self.stats['total_processed']} шт.", flush=True)
        print(f"⚡ СКАЧАНО НАПРЯМУЮ ТУРБО-ПОТОКОМ (REQUESTS): {self.stats['fast_requests_success']} листов", flush=True)
        print(f"🤖 УСПЕШНО ВСКРЫТО БРАУЗЕРОМ (PLAYWRIGHT): {self.stats['playwright_success']} страниц", flush=True)
        print(f"🧹 ОТБРАКОВАНО НЕОТВЕТИВШИХ ССЫЛОК СЕТИ: {self.stats['failed_links']} шт.", flush=True)
        print(f"📈 ОБЩАЯ СКОРОСТЬ СКАНИРОВАНИЯ: {speed_pages:.2f} сайтов в секунду 🌪️", flush=True)
        print(f"⏱️ ВРЕМЯ РАБОТЫ ЦЕХА: Элементы доставлены на Завод за {elapsed:.2f} сек.", flush=True)
        print("-" * 73, flush=True)
        print("🏆 [УСПЕХ] Все сырьевые страницы выкачаны и готовы к дешифровке! Смена сдана! 🤍🏆\n", flush=True)

        return final_contents

if __name__ == "__main__":
    ConfigFetcher().fetch_all()
