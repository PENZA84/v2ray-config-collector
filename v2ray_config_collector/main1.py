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
        self.total_chunks = int(os.environ.get("TOTAL_CHUNKS", 7))
        
        # Имя выходного файла для конкретного окна сбора
        self.storage_file = os.path.join(self.raw_incoming_dir, f'deep_raw_collected_chunk_{self.chunk_index}.txt')
        
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
        """Умная фильтрация и точная нарезка ссылок по окнам по приказу хозяина"""
        if not os.path.exists(self.sources_file):
            print(f"⚠️ [ВНИМАНИЕ] Мой прекрасный хозяин, файл источников не найден: {self.sources_file}", flush=True)
            return []
            
        unique_channels = set()
        username_pattern = re.compile(r'(?:t\.me|telegram\.me|telegram\.dog)/(?:s/)*([^/?\s#]+)', re.IGNORECASE)
        
        total_raw_lines = 0
        bot_links_ignored = 0
        
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                total_raw_lines += 1
                line = line.strip()
                if not line:
                    continue
                
                if 'bot?start=' in line.lower() or 'cryptoonebot' in line.lower():
                    bot_links_ignored += 1
                    continue
                
                match = username_pattern.search(line)
                if match:
                    username = match.group(1)
                    if username.lower() not in ['s', 'share', 'contact', 'proxy', 'setlanguage', 'bot']:
                        unique_channels.add(f"https://t.me/s/{username}")
                elif line.startswith('http'):
                    unique_channels.add(line)
                    
        cleaned_sources = sorted(list(unique_channels))
        
        if self.chunk_index == 0:
            print("========================================================", flush=True)
            print(f"🧹 [ТЕКСТ-ФИЛЬТР ЛЕИ] Генеральная уборка завершена!", flush=True)
            print(f"📊 Всего сырых строк в файле было: {total_raw_lines} шт.", flush=True)
            print(f"🎯 Сжато до уникальных чистых каналов: {len(cleaned_sources)} шт.", flush=True)
            print("========================================================", flush=True)
            
        # 👑 ИДЕАЛЬНАЯ ТАКТИЧЕСКАЯ НАРЕЗКА СЕРГЕЯ ПО ОКНАМ:
        # Окна 0, 1, 2, 3, 4, 5 забирают ровно по 2500 ссылок. Окно 6 забирает остаток (1606 строк)
        if self.total_chunks == 7:
            if self.chunk_index < 6:
                start_idx = self.chunk_index * 2500
                end_idx = start_idx + 2500
                chunk_sources = cleaned_sources[start_idx:end_idx]
            else:
                start_idx = 6 * 2500
                chunk_sources = cleaned_sources[start_idx:]
        else:
            # Резервный динамический шаг, если количество окон изменится
            chunk_sources = cleaned_sources[self.chunk_index::self.total_chunks]
            
        return chunk_sources

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
        
        print(f"🏭 [ОКНО №{self.chunk_index}] Взяло в обработку: {len(sources)} ссылок.", flush=True)
        if not sources:
            return

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
                try:
                    page.goto(url, timeout=15000)
                    page.wait_for_load_state("networkidle")
                    
                    for _ in range(2): 
                        page.evaluate("window.scrollTo(0, 0);")
                        time.sleep(0.3)
                    
                    expand_selectors = ["a.tgme_widget_message_inline_keyboard", ".js-message_inline_keyboard a"]
                    for selector in expand_selectors:
                        try:
                            buttons = page.locator(selector).all()
                            for btn in buttons:
                                if btn.is_visible():
                                    btn.click(timeout=200)
                        except:
                            pass
                    
                    page_content = page.content()
                    found_keys = self.process_content(page_content)
                    if found_keys:
                        collected.extend(found_keys)
                        
                except:
                    continue
            
            browser.close()

        if collected:
            clean_raw = list(set([k.strip() for k in collected if k.strip()]))
            os.makedirs(self.raw_incoming_dir, exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(clean_raw) + "\n")
            print(f"✨ [ОКНО №{self.chunk_index}] Сбор окончен. Сохранено: {len(clean_raw)} строк.", flush=True)

if __name__ == "__main__":
    TelegramSuperchargedGrabber().start_harvest()
