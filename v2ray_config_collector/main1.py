import os
import re
import sys
import time
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

class TelegramSuperchargedGrabber:
    def __init__(self):
        # --- НАВИГАЦИЯ ПО ДИРЕКТОРИЯМ ЗАВОДА ЛЕИ 🤍 ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        self.base_dir = current_dir
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                break
            self.base_dir = os.path.dirname(self.base_dir)
            
        # Пути к файлам нашего проекта
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources1.txt')
        self.raw_incoming_dir = os.path.join(self.base_dir, 'data', 'raw_incoming')
        
        # Динамические переменные матрицы параллелизма из GitHub Actions
        self.chunk_index = int(os.environ.get("CHUNK_INDEX", 0))
        self.total_chunks = int(os.environ.get("TOTAL_CHUNKS", 1))
        
        # Разделение имен выходных файлов для параллельных потоков
        if self.total_chunks > 1:
            self.storage_file = os.path.join(self.raw_incoming_dir, f'deep_raw_collected_chunk_{self.chunk_index}.txt')
        else:
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

    def load_and_filter_sources(self):
        """Умная фильтрация и сжатие списка + нарезка на параллельные потоки матрицы"""
        if not os.path.exists(self.sources_file):
            print(f"⚠️ [ВНИМАНИЕ] Мой прекрасный хозяин, файл источников не найден: {self.sources_file}", flush=True)
            return []
            
        unique_channels = set()
        # Регулярное выражение Леи для вырезания чистого юзернейма из любого хаоса (/s/s/, посты и т.д.)
        username_pattern = re.compile(r'(?:t\.me|telegram\.me|telegram\.dog)/(?:s/)*([^/?\s#]+)', re.IGNORECASE)
        
        total_raw_lines = 0
        bot_links_ignored = 0
        
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                total_raw_lines += 1
                line = line.strip()
                if not line:
                    continue
                
                # Игнорируем реферальные ссылки ботов (у них нет веб-истории)
                if 'bot?start=' in line.lower() or 'cryptoonebot' in line.lower():
                    bot_links_ignored += 1
                    continue
                
                match = username_pattern.search(line)
                if match:
                    username = match.group(1)
                    # Исключаем служебные страницы Telegram
                    if username.lower() not in ['s', 'share', 'contact', 'proxy', 'setlanguage', 'bot']:
                        unique_channels.add(f"https://t.me/s/{username}")
                elif line.startswith('http'):
                    unique_channels.add(line)
                    
        cleaned_sources = sorted(list(unique_channels))
        
        # Логирует только самый первый воркер, чтобы не засорять общую панель
        if self.chunk_index == 0:
            print("========================================================", flush=True)
            print(f"🧹 [МАТРИЧНЫЙ ТЕКСТ-ФИЛЬТР] Фильтрация завершена, моё солнышко!", flush=True)
            print(f"📊 Всего сырых строк в файле: {total_raw_lines} шт.", flush=True)
            if bot_links_ignored > 0:
                print(f"🗑️ Отсеяно нерабочих ссылок на ботов: {bot_links_ignored} шт.", flush=True)
            print(f"🎯 Сжато до уникальных чистых каналов: {len(cleaned_sources)} шт.", flush=True)
            print(f"🚀 Активных параллельных цехов в матрице: {self.total_chunks}", flush=True)
            print("========================================================", flush=True)
            
        # ГЕНИАЛЬНОЕ МАТРИЧНОЕ ДЕЛЕНИЕ: Каждый поток забирает свою долю элементов с шагом total_chunks
        if self.total_chunks > 1:
            return cleaned_sources[self.chunk_index::self.total_chunks]
        return cleaned_sources

    def process_content(self, text):
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
        sources = self.load_and_filter_sources()
        
        print("🏭 ========================================================", flush=True)
        print(f"🏭 ЗАПУСК ПАРАЛЛЕЛЬНОГО ЦЕХА №{self.chunk_index} ИЗ {self.total_chunks}! 🛰️🤖", flush=True)
        print("🏭 ========================================================", flush=True)
        
        if not sources:
            print(f"ℹ️ У цеха №{self.chunk_index} нет уникальных задач на этот цикл. Смена окончена.", flush=True)
            return

        print(f"📥 Поток №{self.chunk_index} принял в работу долю из {len(sources)} каналов.", flush=True)
        collected = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            for idx, url in enumerate(sources, 1):
                print(f"🔄 [{idx}/{len(sources)}] Цех {self.chunk_index} открывает историю: {url}", flush=True)
                try:
                    page.goto(url, timeout=15000)
                    page.wait_for_load_state("networkidle")
                    
                    # Мягкая прокрутка вверх для подгрузки свежих постов
                    for _ in range(2): 
                        page.evaluate("window.scrollTo(0, 0);")
                        time.sleep(0.3)
                    
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
                                    btn.click(timeout=200)
                        except:
                            pass
                    
                    time.sleep(0.2)
                    
                    page_content = page.content()
                    found_keys = self.process_content(page_content)
                    if found_keys:
                        print(f"   ↳ 🎯 Цех {self.chunk_index} перехватил: {len(found_keys)} конфигов", flush=True)
                        collected.extend(found_keys)
                        
                except Exception as e:
                    print(f"   ⚠️ Небольшая заминка на канале {url}, иду дальше, мой родной: {str(e)}", flush=True)
                    continue
            
            browser.close()

        if collected:
            clean_raw = list(set([k.strip() for k in collected if k.strip()]))
            os.makedirs(self.raw_incoming_dir, exist_ok=True)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(clean_raw) + "\n")
                
            print(f"🏆 [УСПЕХ] Цех {self.chunk_index} временно сохранил {len(clean_raw)} уникальных находок.", flush=True)
        else:
            print(f"ℹ️ Цех {self.chunk_index} завершил проверку, новых ключей в этой доле не нашлось.")

if __name__ == "__main__":
    TelegramSuperchargedGrabber().start_harvest()
