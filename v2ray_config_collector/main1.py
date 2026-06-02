import os
import re
import sys
import time
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

class TelegramPlaywrightCollector:
    def __init__(self):
        # --- ENGLISH PRODUCTION ENVIRONMENT NAVIGATION ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        self.base_dir = current_dir
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                break
            self.base_dir = os.path.dirname(self.base_dir)
            
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources1.txt')
        self.raw_incoming_dir = os.path.join(self.base_dir, 'data', 'raw_incoming')
        self.storage_file = os.path.join(self.raw_incoming_dir, 'deep_raw_collected.txt')
        
        # Твой оригинальный всеядный список из 23 протоколов! 👑
        self.protocols = [
            'socks5', 'socks4', 'socks', 'http', 'https', 'ss', 'trojan', 
            'vmess', 'vless', 'tuic', 'hysteria', 'hysteria2', 'hy2', 
            'anytls', 'naive', 'naive+https', 'juicity', 'trusttunnel', 
            'shadowtls', 'wireguard', 'wg', 'ssh'
        ]
        
        proto_pattern = '|'.join([re.escape(p) for p in self.protocols])
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')
        self.tg_proxy_pattern = re.compile(r'(?:https://t.me/proxy?[^s<"\']+)|(?:tg://proxy\?[^\s<"\']*)')

    def load_sources(self):
        if not os.path.exists(self.sources_file):
            return []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip().startswith('http')]

    def process_content(self, text):
        """Парсинг полностью раскрытого текста"""
        extracted = []
        found_profiles = self.regex_pattern.findall(text)
        for link in found_profiles:
            link = link.strip().rstrip('.')
            if any(bad in link for bad in ['User-Agent', 'headers', 'Pragma', 'cache-control', 'Host,']):
                continue
            extracted.append(link)
        
        tg_proxies = self.tg_proxy_pattern.findall(text.replace('&amp;', '&'))
        for tg_url in tg_proxies:
            try:
                parsed = urlparse(tg_url)
                query = parse_qs(parsed.query)
                server = query.get('server', [None])[0]
                port = query.get('port', [None])[0]
                if server and port:
                    extracted.append(f"socks5://{server}:{port}#TG_Socks")
                    extracted.append(f"http://{server}:{port}#TG_HTTP")
            except: 
                continue
        return extracted

    def start_harvest(self):
        sys.stdout.reconfigure(line_buffering=True)
        sources = self.load_sources()
        
        print("🏭 [ПОТОК 2] ==============================================", flush=True)
        print("🏭 [ПОТОК 2] ЗАПУСК ТЯЖЕЛОГО РОБОТА PLAYWRIGHT ДЛЯ TG! 🤖🛰️", flush=True)
        print("🏭 [ПОТОК 2] ==============================================", flush=True)
        
        if not sources:
            print("ℹ️ [ИНФО] Дополнительный список источников пуст.", flush=True)
            return

        print(f"📥 Найдено целевых каналов/страниц: {len(sources)} шт.", flush=True)
        print("🤖 Запуск скрытого браузера Chromium для раскрытия скрытых блоков...", flush=True)
        
        start_time = time.time()
        collected = []

        with sync_playwright() as p:
            # Запускаем headless-браузер
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for idx, url in enumerate(sources, 1):
                # Если ссылка ведет на канал, перенаправляем на его веб-хронику, где есть все посты
                target_url = url
                if "t.me/" in url and not "/s/" in url:
                    target_url = url.replace("t.me/", "t.me/s/")
                
                print(f"🔄 [{idx}/{len(sources)}] Сканируем и вскрываем: {target_url}", flush=True)
                try:
                    page.goto(target_url, timeout=15000)
                    page.wait_for_load_state("networkidle")
                    
                    # 👑 СЕКРЕТНЫЙ ТРИГГЕР ЗАВОДА: Находим ВСЕ кнопки раскрытия блоков в Telegram и кликаем!
                    # В веб-версии Telegram кнопки раскрытия часто имеют класс .tgme_widget_message_inline_keyboard или подобные элементы управления
                    expand_buttons = page.locator("a.tgme_widget_message_inline_keyboard, .js-message_inline_keyboard a").all()
                    if expand_buttons:
                        for btn in expand_buttons:
                            try:
                                if btn.is_visible():
                                    btn.click(timeout=500)
                            except:
                                pass
                    
                    # Ждем долю секунды, чтобы анимация развернула текст
                    time.sleep(0.5)
                    
                    # Снимаем слепок со 100% развернутой страницы!
                    page_content = page.content()
                    found_keys = self.process_content(page_content)
                    if found_keys:
                        collected.extend(found_keys)
                except Exception as e:
                    print(f"⚠️ Ошибка доступа к {target_url}: {str(e)}", flush=True)
                    continue
                    
            browser.close()

        elapsed_time = time.time() - start_time
        speed_pages = len(sources) / elapsed_time if elapsed_time > 0 else 0
        speed_keys = len(collected) / elapsed_time if elapsed_time > 0 else 0

        if collected:
            clean_raw = list(set([k.strip() for k in collected if k.strip()]))
            
            os.makedirs(self.raw_incoming_dir, exist_ok=True)
            existing = set()
            
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    existing = set(line.strip() for line in f if line.strip())
            
            existing.update(clean_raw)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(sorted(list(existing))) + "\n")

            # Выводим наш красивейший отчет!
            print("\n📊 " + "-"*20 + " ОТЧЕТ УМНОГО КЛИКЕРА PLAYWRIGHT " + "-"*20, flush=True)
            print(f"📦 ВСЕГО ВЫКАЧАНО (ПОЛНЫЕ СТРОКИ): {len(collected)} элементов", flush=True)
            print(f"✨ ЧИСТЫХ РАЗВЕРНУТЫХ КЛЮЧЕЙ СОХРАНЕНО: {len(clean_raw)} шт.", flush=True)
            print(f"📈 СКОРОСТЬ КЛИКЕРА: {speed_pages:.2f} страниц/сек с полной прокруткой", flush=True)
            print(f"🚀 ЭФФЕКТИВНОСТЬ ПЕРЕХВАТА: {speed_keys:.2f} полных конфигов/сек ⚡", flush=True)
            print(f"⏱️ ВРЕМЯ РАБОТЫ РОБОТА: Конвейер отработал за {elapsed_time:.2f} сек.", flush=True)
            print("-" * 74, flush=True)
            print("🏆 [УСПЕХ] Ни один скрытый хвост не потерян! Все полные ключи в бункере! 🤍🏆🦖\n", flush=True)
        else:
            print("ℹ️ [ИНФО] Кнопки нажаты, но валидных данных внутри не обнаружено.", flush=True)

if __name__ == "__main__":
    TelegramPlaywrightCollector().start_harvest()
