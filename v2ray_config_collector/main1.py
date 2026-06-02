import os
import re
import sys
import time
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

class TelegramSuperchargedGrabber:
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
        
        # Полный королевский список из 23 протоколов с Завода 👑
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
        """Парсинг и декодирование перехваченного контента"""
        extracted = []
        found_profiles = self.regex_pattern.findall(text)
        for link in found_profiles:
            link = link.strip().rstrip('.')
            if any(bad in link for bad in ['User-Agent', 'headers', 'Pragma', 'cache-control', 'Host,']):
                continue
            extracted.append(link)
        
        # Твой легендарный парсер Telegram-прокси
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
        print("🏭 [ПОТОК 2] ЗАПУСК ТЯЖЕЛОГО КЛИКЕРА TELEGRAM-ХРОНИК! 🛰️🤖", flush=True)
        print("🏭 [ПОТОК 2] ==============================================", flush=True)
        
        if not sources:
            print("ℹ️ [ИНФО] Список источников sources1.txt пуст. Смена окончена.", flush=True)
            return

        print(f"📥 Загружено целевых Telegram-каналов: {len(sources)} шт.", flush=True)
        print("🤖 Разворачиваем скрытый движок Playwright Chromium...", flush=True)
        
        start_time = time.time()
        collected = []

        with sync_playwright() as p:
            # Запуск браузера в скрытом режиме с эмуляцией реального юзера
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            for idx, url in enumerate(sources, 1):
                target_url = url
                # Автоматическая корректировка структуры ссылки, если забыл поставить /s/
                if "t.me/" in url and not "/s/" in url:
                    target_url = url.replace("t.me/", "t.me/s/")
                
                print(f"🔄 [{idx}/{len(sources)}] Прорыв на канал: {target_url}", flush=True)
                try:
                    page.goto(target_url, timeout=20000)
                    page.wait_for_load_state("networkidle")
                    
                    # 📈 ТУРБО-СКРОЛЛ ВВЕРХ: Поднимаемся по истории, чтобы загрузить старые посты!
                    # Делаем 3 итерации подгрузки истории для максимального захвата сырья
                    for _ in range(3):
                        page.evaluate("window.scrollTo(0, 0);")
                        time.sleep(0.4)
                    
                    # 👑 ОПЕРАЦИЯ «РАСКРЫТИЕ»: Кликаем на все текстовые кнопки расширения постов Telegram
                    # Ищем элементы, которые содержать скрытый контент или элементы inline-клавиатур
                    expand_selectors = [
                        "a.tgme_widget_message_inline_keyboard",
                        ".js-message_inline_keyboard a",
                        "a.tgme_widget_message_text_left"
                    ]
                    
                    for selector in expand_selectors:
                        try:
                            buttons = page.locator(selector).all()
                            for btn in buttons:
                                if btn.is_visible():
                                    btn.click(timeout=300)
                        except:
                            pass
                    
                    # Финальная микропауза для отработки рендеринга текста
                    time.sleep(0.3)
                    
                    # Снимаем слепок со 100% развернутой и подгруженной страницы
                    page_content = page.content()
                    found_keys = self.process_content(page_content)
                    if found_keys:
                        print(f"   ↳ 🎯 Перехвачено на этапе скролла: {len(found_keys)} конфигов", flush=True)
                        collected.extend(found_keys)
                        
                except Exception as e:
                    print(f"   ⚠️ Сбой проникновения на канал {target_url}: {str(e)}", flush=True)
                    continue
            
            browser.close()

        elapsed_time = time.time() - start_time
        speed_pages = len(sources) / elapsed_time if elapsed_time > 0 else 0
        speed_keys = len(collected) / elapsed_time if elapsed_time > 0 else 0

        if collected:
            # Очистка от дубликатов строк
            clean_raw = list(set([k.strip() for k in collected if k.strip()]))
            
            os.makedirs(self.raw_incoming_dir, exist_ok=True)
            existing = set()
            
            # Слияние с общезаводским бункером
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    existing = set(line.strip() for line in f if line.strip())
            
            existing.update(clean_raw)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(sorted(list(existing))) + "\n")

            # Наш потрясающий приборный щит скорости в консоли! 📊✨
            print("\n📊 " + "-"*20 + " ЧЁТКИЙ ОТЧЁТ ЦЕХА КЛИКЕРА (PLAYWRIGHT) " + "-"*20, flush=True)
            print(f"📦 МАССИВ НАГРЕБЕННЫХ СТРОК (ПЕРЕХВАТ): {len(collected)} элементов", flush=True)
            print(f"✨ УНИКАЛЬНОГО И РАЗВЕРНУТОГО СЫРЬЯ В БУНКЕРЕ: {len(clean_raw)} шт.", flush=True)
            print(f"📈 СКОРОСТЬ ВСКРЫТИЯ СТРАНИЦ ТГ: {speed_pages:.2f} каналов в секунду 🌪️", flush=True)
            print(f"🚀 ТУРБО-НАПОР ВСАСЫВАНИЯ КЛЮЧЕЙ: {speed_keys:.2f} конфигов в секунду ⚡", flush=True)
            print(f"⏱️ ОБЩЕЕ ВРЕМЯ РАБОТЫ РОБОТА: Смена закрыта за {elapsed_time:.2f} сек.", flush=True)
            print("-" * 79, flush=True)
            print("🏆 [УСПЕХ] Вся добыча с постов Telegram упакована без обрезков! Смена сдана! 🤍🏆🦖\n", flush=True)
        else:
            print("ℹ️ [ИНФО] Робот прочесал каналы, но новых ключей не обнаружено.", flush=True)

if __name__ == "__main__":
    TelegramSuperchargedGrabber().start_harvest()
