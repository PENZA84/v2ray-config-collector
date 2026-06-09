import os
import sys
import time
import base64
from collections import defaultdict
from playwright.sync_api import sync_playwright

class GitHubFactoryGrabber:
    def __init__(self):
        # --- НАВИГАЦИЯ ПО НАШЕМУ ЗАВОДУ ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        # Динамический поиск корня репозитория
        self.base_dir = current_dir
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                break
            self.base_dir = os.path.dirname(self.base_dir)

        # ЧЁТКОЕ РАСПРЕДЕЛЕНИЕ ЦЕХОВ И НАШЕЙ ИМЕННОЙ МИШЕНИ
        self.sources_dir = os.path.join(self.base_dir, 'data', 'sources')
        self.targets_file = os.path.join(self.sources_dir, 'grabber_targets.txt') # СТРОГО НАШ ФАЙЛ ССЫЛОК!
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.input_file = os.path.join(self.base_dir, 'data', 'raw_incoming', 'deep_raw_collected.txt')
        
        # Гарантируем наличие структуры папок при старте на виртуалке
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.sources_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.input_file), exist_ok=True)
        
        self.protocols = [
            'socks5', 'socks4', 'socks', 'http', 'https', 'ss', 'trojan', 
            'vmess', 'vless', 'tuic', 'hysteria', 'hysteria2', 'hy2', 
            'anytls', 'naive', 'naive+https', 'juicity', 'trusttunnel', 
            'shadowtls', 'wireguard', 'wg', 'ssh'
        ]
        
        self.stats = {
            'total_raw_lines': 0,
            'blocked_tg_proxies': 0,
            'valid_extracted': 0,
            'saved_lines': 0,
            'cleared_for_n': 0,
            'clicked_sources': 0
        }
        self.proto_stats = defaultdict(int)

    def verify_factory_lanes(self):
        """🔍 ОТК: Контроль изоляции источников"""
        print("\n🔍 ================= [КОНТРОЛЬ ОТК НАШЕГО ЗАВОДА] =================", flush=True)
        print(f"🏭 Корень репозитория: {self.base_dir}", flush=True)
        print(f"📂 Общий цех источников: {self.sources_dir}", flush=True)
        print(f"🎯 Личный рацион Граббера: {self.targets_file}", flush=True)
        print(f"📦 Склад готовой продукции unique: {self.output_dir}", flush=True)
        
        # Проверяем, на месте ли именной файл Граббера
        if os.path.exists(self.targets_file):
            print("✅ Именной файл grabber_targets.txt ОБНАРУЖЕН и готов к производству!", flush=True)
        else:
            print("⚠️ ВНИМАНИЕ: grabber_targets.txt отсутствует в data/sources/! Создаю пустой бланк.", flush=True)
            with open(self.targets_file, 'w', encoding='utf-8') as f:
                f.write("# Добавь сюда китайские ссылки для обкликивания браузером\n")
                
        print("✅ ВЕРИФИКАЦИЯ ЗАВЕРШЕНА: Граббер изолирован, конфликты с майнами исключены!\n", flush=True)

    def decode_base64_safely(self, content):
        if not content:
            return ""
        try:
            clean = content.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            if len(clean) > 30 * 1024 * 1024:
                return content
            missing_padding = len(clean) % 4
            if missing_padding:
                clean += '=' * (4 - missing_padding)
            return base64.b64decode(clean).decode('utf-8', errors='ignore')
        except:
            return content

    def fast_extract_configs(self, text):
        extracted = []
        if not text:
            return extracted
        lines = text.split('\n')
        self.stats['total_raw_lines'] += len(lines)
        for line in lines:
            line_clean = line.strip()
            if not line_clean or '://' not in line_clean:
                continue
            is_valid_proto = False
            for proto in self.protocols:
                if line_clean.lower().startswith(f"{proto}://"):
                    is_valid_proto = True
                    break
            if not is_valid_proto:
                continue
            if "tg://proxy" in line_clean or "t.me/proxy" in line_clean or "proxy?" in line_clean:
                self.stats['blocked_tg_proxies'] += 1
                continue
            extracted.append(line_clean)
        return extracted

    def download_and_click_targets(self):
        """Браузерный модуль: работает СТРОГО по файлу grabber_targets.txt"""
        print(f"🌐 [Цех Кликера]: Вычитываем цели из {os.path.basename(self.targets_file)}...", flush=True)
        
        targets = []
        try:
            with open(self.targets_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_clean = line.strip()
                    if line_clean and not line_clean.startswith('#') and '://' in line_clean:
                        targets.append(line_clean)
        except Exception as e:
            print(f"❌ Ошибка чтения файла целей: {e}", flush=True)
            return

        targets = list(set(targets))
        if not targets:
            print("ℹ️ В grabber_targets.txt нет ссылок для обработки кликером. Смена окончена.", flush=True)
            return

        print(f"🚀 Запуск Playwright. Берем в работу {len(targets)} целевых URL!", flush=True)
        collected_raw_data = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            for url in targets:
                try:
                    print(f"🕵️‍♂️ Робот открывает цель: {url[:60]}...", flush=True)
                    page = context.new_page()
                    page.goto(url, timeout=45000, wait_until="networkidle")
                    time.sleep(4)
                    
                    buttons = page.locator("button, a, .btn, [role='button']").all()
                    for btn in buttons:
                        try:
                            text = btn.inner_text().strip()
                            if any(x in text for x in ["复制", "获取", "Get", "Copy", "🔑", "Показать"]):
                                print(f"  👆 Найдена кнопка [{text}] -> Кликаю!", flush=True)
                                btn.click(timeout=3000)
                                time.sleep(1.5)
                        except:
                            continue

                    page_content = page.content()
                    collected_raw_data.append(page_content)
                    self.stats['clicked_sources'] += 1
                    page.close()
                except Exception as e:
                    print(f"  ❌ Осечка на странице: {e}", flush=True)
            
            browser.close()

        combined_raw = "\n".join(collected_raw_data)
        if combined_raw.strip():
            with open(self.input_file, "a", encoding="utf-8") as f:
                f.write("\n" + combined_raw + "\n")
            print(f"✅ Сырьё успешно упаковано в бункер. Отработано сайтов: {self.stats['clicked_sources']} шт.", flush=True)

    def save_to_txt_shelves(self, configs):
        if not configs:
            return
        buckets = defaultdict(list)
        for link in configs:
            for proto in self.protocols:
                if link.lower().startswith(f"{proto}://"):
                    buckets[proto].append(link)
                    self.proto_stats[proto] += 1
                    break

        max_bytes_per_file = 90 * 1024 * 1024 

        for proto, lines in buckets.items():
            safe_proto = proto.replace('+', '_')
            base_filename = f"grabber_{safe_proto}"
            
            existing_lines = []
            main_file_path = os.path.join(self.output_dir, f"{base_filename}.txt")
            
            if os.path.exists(main_file_path):
                try:
                    with open(main_file_path, 'r', encoding='utf-8') as f:
                        existing_lines.extend([l.strip() for l in f if l.strip()])
                except:
                    pass
            
            chunk_idx = 1
            while True:
                chunk_file = os.path.join(self.output_dir, f"{base_filename}_{chunk_idx}.txt")
                if os.path.exists(chunk_file):
                    try:
                        with open(chunk_file, 'r', encoding='utf-8') as f:
                            existing_lines.extend([l.strip() for l in f if l.strip()])
                        os.remove(chunk_file)
                    except:
                        pass
                    chunk_idx += 1
                else:
                    break

            total_monolith = list(set(existing_lines + lines))
            if proto in ['http', 'https', 'socks', 'socks4', 'socks5']:
                self.stats['cleared_for_n'] += len(lines)
            
            sorted_lines = sorted(total_monolith)
            all_chunks = []
            current_chunk = []
            current_size = 0
            
            for line in sorted_lines:
                line_str = line + "\n"
                line_bytes = len(line_str.encode('utf-8'))
                if current_size + line_bytes > max_bytes_per_file:
                    all_chunks.append(current_chunk)
                    current_chunk = [line]
                    current_size = line_bytes
                else:
                    current_chunk.append(line)
                    current_size += line_bytes
            if current_chunk:
                all_chunks.append(current_chunk)
            
            if len(all_chunks) <= 1 and all_chunks:
                file_path = os.path.join(self.output_dir, f"{base_filename}.txt")
                tmp_file = file_path + ".tmp"
                with open(tmp_file, 'w', encoding='utf-8') as out_f:
                    out_f.write("\n".join(all_chunks[0]) + "\n")
                os.replace(tmp_file, file_path)
            else:
                if os.path.exists(main_file_path):
                    try: os.remove(main_file_path)
                    except: pass
                for idx, chunk in enumerate(all_chunks, start=1):
                    file_path = os.path.join(self.output_dir, f"{base_filename}_{idx}.txt")
                    tmp_file = file_path + ".tmp"
                    with open(tmp_file, 'w', encoding='utf-8') as out_f:
                        out_f.write("\n".join(chunk) + "\n")
                    os.replace(tmp_file, file_path)
                    
            self.stats['saved_lines'] += len(lines)

    def run_grabber_production(self):
        sys.stdout.reconfigure(line_buffering=True)
        print("🏭 [ЗАВОД] Запуск автономного Граббера по ЕГО ИМЕННЫМ ИСТОЧНИКАМ... 🚀", flush=True)
        start_time = time.time()
        
        self.verify_factory_lanes()
        self.download_and_click_targets()
        
        if not os.path.exists(self.input_file):
            print(f"ℹ️ Бункер сырья пуст: {self.input_file}", flush=True)
            return

        with open(self.input_file, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        if not raw_content.strip():
            print("ℹ️ Обрабатывать нечего.")
            return

        decoded = self.decode_base64_safely(raw_content)
        all_found_configs = self.fast_extract_configs(decoded)

        if all_found_configs:
            unique_incoming = list(set(all_found_configs))
            self.stats['valid_extracted'] = len(unique_incoming)
            self.save_to_txt_shelves(unique_incoming)

        try:
            with open(self.input_file, 'w', encoding='utf-8') as f:
                f.write("")
            print("🧹 Временный бункер сырья зачищен.")
        except Exception as e:
            print(f"⚠️ Ошибка зачистки бункера: {e}")

        elapsed = time.time() - start_time
        print("\n📊 " + "-"*20 + " ОТЧЁТ ИЗОЛИРОВАННОГО ГРАББЕРА " + "-"*20, flush=True)
        print(f"🎯 ССЫЛОК ИЗ GRABBER_TARGETS.TXTОБРАБОТАНО: {self.stats['clicked_sources']} шт.", flush=True)
        print(f"📦 ВСЕГО СТРОК СЫРЬЯ ПРОСКАНИРОВАНО: {self.stats['total_raw_lines']} шт.", flush=True)
        print(f"📥 ЧИСТЫХ ПРОКСИ ИЗВЛЕЧЕНО КЛИКЕРОМ: {self.stats['valid_extracted']} шт.", flush=True)
        print(f"✨ СОХРАНЕНО НА СКЛАД UNIQUE С ПРЕФИКСОМ GRABBER_: {self.stats['saved_lines']} шт.", flush=True)
        print(f"⏱️ ВРЕМЯ РАБОТЫ СМЕНЫ: {elapsed:.4f} сек.", flush=True)
        print("-" * 87, flush=True)

if __name__ == "__main__":
    GitHubFactoryGrabber().run_grabber_production()
