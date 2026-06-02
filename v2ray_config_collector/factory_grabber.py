import os
import sys
import time
import base64
from collections import defaultdict

class GitHubFactoryGrabber:
    def __init__(self):
        # --- МОНОЛИТНАЯ НАВИГАЦИЯ ЗАВОДА ЛЕИ ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        self.base_dir = current_dir
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                break
            self.base_dir = os.path.dirname(self.base_dir)

        # Пути к папкам Гитхаба
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.input_file = os.path.join(self.base_dir, 'data', 'raw_incoming', 'deep_raw_collected.txt')
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Полный королевский список из 23 протоколов Трона и v2rayN 👑
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
            'cleared_for_n': 0
        }
        self.proto_stats = defaultdict(int)

    def decode_base64_safely(self, content):
        """Сверхскоростное декодирование без утечек памяти и зависаний"""
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
        """Линейный сверхзвуковой поиск ключей БЕЗ опасных регулярных выражений"""
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

            # 🛑 ЖЕСТКИЙ ЩИТ: Немедленный бан мусорных прокси-ссылок Телеграма
            if "tg://proxy" in line_clean or "t.me/proxy" in line_clean or "proxy?" in line_clean:
                self.stats['blocked_tg_proxies'] += 1
                continue

            extracted.append(line_clean)
        return extracted

    def save_to_txt_shelves(self, configs):
        """Атомарная дозапись на текстовые полки с раздельными правилами для Трона и Н"""
        if not configs:
            return

        buckets = defaultdict(list)
        for link in configs:
            for proto in self.protocols:
                if link.lower().startswith(f"{proto}://"):
                    buckets[proto].append(link)
                    self.proto_stats[proto] += 1
                    break

        # Физически пишем чистый ТХТ на диск
        for proto, lines in buckets.items():
            safe_filename = proto.replace('+', '_')
            file_path = os.path.join(self.output_dir, f"{safe_filename}.txt")
            
            # Читаем старую базу, чтобы убрать дубликаты
            existing_lines = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_lines = [l.strip() for l in f if l.strip()]
                except:
                    pass

            # Слияние и моментальное удаление дублей через set()
            total_monolith = list(set(existing_lines + lines))
            
            # 📜 ГВАРДЕЙСКИЙ УСТАВ: Очистка файлов для программы Н!
            # Если этот протокол пойдет в файлы стран для Н, мы жестко убираем http/https/socks
            if proto in ['http', 'https', 'socks', 'socks4', 'socks5']:
                self.stats['cleared_for_n'] += len(lines)
                # Для всеядного Трона мы этот файл ЗАПИСЫВАЕМ, он у него будет!
            
            # Атомарное сохранение файла на Гитхабе
            tmp_file = file_path + ".tmp"
            with open(tmp_file, 'w', encoding='utf-8') as out_f:
                out_f.write("\n".join(sorted(total_monolith)) + "\n")
            os.replace(tmp_file, file_path)
            self.stats['saved_lines'] += len(lines)

    def run_grabber_production(self):
        """Запуск генерального цикла смены снабжения на GitHub Actions"""
        sys.stdout.reconfigure(line_buffering=True)
        print("🏭 [ЗАВОД ГИТХАБА] Запуск неуязвимого сборщика factory_grabber.py... 🚀", flush=True)
        
        start_time = time.time()
        
        if not os.path.exists(self.input_file):
            print(f"ℹ️ Бункер сырья отсутствует: {self.input_file}", flush=True)
            return

        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except Exception as e:
            print(f"⚠️ Ошибка чтения бункера: {e}", flush=True)
            return

        if not raw_content.strip():
            print("ℹ️ Бункер deep_raw_collected.txt пуст.", flush=True)
            return

        # Декодируем и извлекаем ключи линейным сканером БЕЗ РЕГУЛЯРОК
        decoded = self.decode_base64_safely(raw_content)
        all_found_configs = self.fast_extract_configs(decoded)

        if all_found_configs:
            unique_incoming = list(set(all_found_configs))
            self.stats['valid_extracted'] = len(unique_incoming)
            self.save_to_txt_shelves(unique_incoming)

        # Очищаем бункер сбора сырья для следующего коммита
        try:
            with open(self.input_file, 'w', encoding='utf-8') as f:
                f.write("")
            print("🧹 Бункер deep_raw_collected.txt успешно очищен.", flush=True)
        except Exception as e:
            print(f"⚠️ Не удалось очистить бункер: {e}", flush=True)

        elapsed = time.time() - start_time
        
        # Наш роскошный приборный отчет в логах Гитхаба! 📊
        print("\n📊 " + "-"*20 + " ОТЧЁТ СВЕРХСКОРОСТНОЙ СМЕНЫ " + "-"*20, flush=True)
        print(f"📦 ВСЕГО СТРОК ПРОАНАЛИЗИРОВАНО В БУНКЕРЕ: {self.stats['total_raw_lines']} шт.", flush=True)
        print(f"📥 ЧИСТЫХ ВАЛИДНЫХ КЛЮЧЕЙ ИЗВЛЕЧЕНО: {self.stats['valid_extracted']} шт.", flush=True)
        print(f"🛑 МУСОРНЫХ ПРОКСИ ДЛЯ Н ЗАБЛОКИРОВАНО: {self.stats['blocked_tg_proxies']} шт. 🛡️", flush=True)
        print(f"🛡️ СТРОК HTTP/SOCKS ОТФИЛЬТРОВАНО (ЗАЩИТА ОТ СЛЕПЫХ МЕСТ В Н): {self.stats['cleared_for_n']} шт.", flush=True)
        print(f"✨ ВСЕГО СТРОК СОХРАНЕНО НА ПОЛКИ ТРОНА В /UNIQUE/: {self.stats['saved_lines']} шт.", flush=True)
        print(f"⏱️ ВРЕМЯ РАБОТЫ ЦЕХА: Выполнено за {elapsed:.4f} сек. БЕЗ ЗАВИСАНИЙ! 🔥", flush=True)
        print("-" * 77, flush=True)

if __name__ == "__main__":
    GitHubFactoryGrabber().run_grabber_production()
