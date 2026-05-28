import os
import re
import sys
import time
from playwright.sync_api import sync_playwright

class DynamicWebWalker:
    def __init__(self):
        # Настройка путей Завода
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources.txt')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_file = os.path.join(self.output_dir, 'deduplicated.txt')
        
        # Полный список протоколов Трона для поиска в тексте
        self.protocols = [
            'naive+https', 'shadowtls', 'trusttunnel', 'hysteria2', 'wireguard', 
            'juicity', 'socks5', 'socks4', 'anytls', 'vmess', 'vless', 'trojan', 
            'naive', 'socks', 'https', 'http', 'tuic', 'hy2', 'ssh', 'wg', 'ss'
        ]
        
        proto_pattern = '|'.join([re.escape(p) for p in self.protocols])
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')

    def load_sources(self):
        """Загрузка сайтов для глубокого обхода"""
        if not os.path.exists(self.sources_file):
            return []
        links = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('http') and not any(ext in line for ext in ['.txt', '.yaml']):
                    # Берем только главные страницы блогов/сайтов, где надо кликать
                    links.append(line)
        return links

    def extract_proxies(self, text):
        """Поиск протоколов в открывшемся тексте страницы"""
        found = self.regex_pattern.findall(text)
        return [l.strip().rstrip('.') for l in found if l.strip()]

    def walk_and_click(self, url, page):
        """Глубокий ходок: заходит на сайт, ищет статьи, кликает по кнопкам"""
        extracted = []
        print(f"🌐 Ходок заходит на: {url}", flush=True)
        
        try:
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            time.sleep(3) # Даем скриптам прогрузиться
            
            # 1. Собираем ссылки на свежие статьи (как на твоем скрине от 28 мая)
            # Ищем элементы, которые могут быть кнопками или ссылками на посты
            elements = page.query_selector_all("a")
            sub_links = []
            
            for el in elements:
                href = el.get_attribute("href")
                text = el.inner_text().lower()
                if href and any(k in text or k in href for k in ['node', 'proxy', 'free', 'clash', 'v2ray', 'sub', 'airport', 'марта', 'мая', 'июня']):
                    full_url = href if href.startswith('http') else url + href
                    sub_links.append(full_url)
            
            # Убираем дубли подстраниц и берем топ-3 самых свежих
            sub_links = list(set(sub_links))[:3]
            
            if not sub_links:
                # Если подстраниц нет, работаем с текущей страницей
                sub_links = [url]

            for sub_url in sub_links:
                print(f"  📥 Переход во внутреннюю статью: {sub_url}", flush=True)
                page.goto(sub_url, timeout=20000, wait_until="networkidle")
                time.sleep(2)
                
                # --- БЛОК НАЖАТИЯ НА КНОПКИ РАСКРЫТИЯ ---
                # Ищем кнопки «Показать код», «Раскрыть», «Copy», «Читать далее»
                buttons = page.query_selector_all("button, input[type='button'], a.more-link, .read-more")
                for btn in buttons:
                    try:
                        btn_text = btn.inner_text().lower()
                        if any(k in btn_text for k in ['показать', 'раскрыть', 'код', 'show', 'more', 'click', 'copy', 'read']):
                            btn.click(timeout=2000)
                            time.sleep(1.5)
                            print("    🔘 Нажата кнопка раскрытия контента!", flush=True)
                    except:
                        continue
                
                # Забираем весь финальный текст страницы после кликов
                page_text = page.content()
                found_nodes = self.extract_proxies(page_text)
                extracted.extend(found_nodes)
                
        except Exception as e:
            print(f"  ❌ Ошибка при обработке страницы: {e}", flush=True)
            
        return extracted

    def run(self):
        sys.stdout.reconfigure(line_buffering=True)
        sources = self.load_sources()
        
        if not sources:
            print("⚠️ Нет подходящих динамических сайтов в sources.txt", flush=True)
            return

        print(f"🚀 Запуск Ходока на Playwright. Найдено динамических сайтов: {len(sources)}", flush=True)
        all_collected = []

        # Запуск скрытого браузера Chromium
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Эмулируем обычный ПК, чтобы сайты не выдавали капчу
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            for url in sources:
                nodes = self.walk_and_click(url, page)
                all_collected.extend(nodes)
                
            browser.close()

        if all_collected:
            print(f"💎 Ходок успешно вытащил {len(all_collected)} строк из динамических страниц!", flush=True)
            
            # Дописываем результаты в наш общий файл deduplicated.txt для последующей очистки Гвардом
            os.makedirs(self.output_dir, exist_ok=True)
            
            existing_lines = []
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_lines = [line.strip() for line in f if line.strip()]
            
            # Объединяем старое и новое
            final_pool = existing_lines + all_collected
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(final_pool))
            print("📦 Все добытые протоколы успешно слиты в deduplicated.txt!", flush=True)
        else:
            print("❌ Ходок обошел сайты, но скрытых протоколов не обнаружил.", flush=True)

if __name__ == "__main__":
    DynamicWebWalker().run()
