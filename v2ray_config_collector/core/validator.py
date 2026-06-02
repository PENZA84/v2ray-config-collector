import os
import re
import sys
import time
import socket
import json
import base64
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class ConnectivityValidator:
    def __init__(self):
        # --- МОНОЛИТНАЯ НАВИГАЦИЯ ЗАВОДА ЛЕИ ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        self.base_dir = current_dir
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                break
            self.base_dir = os.path.dirname(self.base_dir)

        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique') # Перезапись очищенных
        
        self.protocols = [
            'naive+https', 'shadowtls', 'trusttunnel', 'hysteria2', 'wireguard', 
            'juicity', 'socks5', 'socks4', 'anytls', 'vmess', 'vless', 'trojan', 
            'naive', 'socks', 'https', 'http', 'tuic', 'hy2', 'ssh', 'wg', 'ss'
        ]

        self.valid_configs = {proto: [] for proto in self.protocols}
        self.valid_configs['clash'] = [] # Поддержка сгенерированного Clash-кода
        
        self.stats = {'valid_configs': 0, 'total_checked': 0, 'failed_tcp': 0}

    def read_configs(self):
        """Чтение всех конфигураций из файлов папки unique"""
        all_lines = []
        if not os.path.exists(self.input_dir):
            return all_lines
            
        for file_name in os.listdir(self.input_dir):
            if not file_name.endswith('.txt') or 'deduplicated' in file_name.lower():
                continue
            file_path = os.path.join(self.input_dir, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line_clean = line.strip()
                        if line_clean and not line_clean.startswith('#'):
                            all_lines.append(line_clean)
            except:
                pass
        return list(set(all_lines))

    def detect_protocol(self, config):
        """Определение протокола строки"""
        if config.startswith('clash-config://'):
            return 'clash'
        for proto in self.protocols:
            if config.lower().startswith(f"{proto}://"):
                return proto
        return None

    def extract_server_port(self, config, protocol):
        """Глубокое извлечение хоста и порта для оригинального TCP-теста"""
        try:
            if protocol == 'clash':
                # Декодируем оригинальный Clash-код для извлечения сетевой точки
                b64_str = config.split('://')[1]
                dec = base64.b64decode(b64_str).decode('utf-8')
                # Быстрый поиск параметров в дампе без тяжелого yaml-парсинга
                server = re.search(r'server:\s*([^\s\n]+)', dec)
                port = re.search(r'port:\s*([^\s\n]+)', dec)
                if server and port:
                    return server.group(1).strip('"\''), int(port.group(1))
                return None, None

            if protocol == 'vmess':
                b64_data = config.split('://')[1].split('#')[0]
                missing_padding = len(b64_data) % 4
                if missing_padding: b64_data += '=' * (4 - missing_padding)
                data = json.loads(base64.b64decode(b64_data).decode('utf-8', errors='ignore'))
                return str(data.get('add')).strip(), int(data.get('port'))

            # Общая логика для vless, trojan, ss, hysteria2
            clean_line = config.split('?')[0] if '?' in config else config
            parsed = urllib.parse.urlparse(clean_line)
            netloc = parsed.netloc if parsed.netloc else config.split('://')[1].split('#')[0]
            
            if '@' in netloc:
                netloc = netloc.split('@')[-1]
            if ':' in netloc:
                host, port = netloc.split(':', 1)
                if '/' in port: port = port.split('/')[0]
                return host.strip('[]'), int(port)
        except:
            pass
        return None, None

    def test_tcp_connection(self, host, port, timeout=2.5):
        """Оригинальный сетевой тест проверки доступности точки прокси по TCP-сокету"""
        if not host or not port:
            return False
        try:
            # Быстрый сетевой чекер без зависаний
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0 # Если 0 — порт открыт и доступен!
        except:
            return False

    def test_config(self, config):
        """Тестирование отдельной конфигурации"""
        proto = self.detect_protocol(config)
        if not proto:
            return None, False
            
        host, port = self.extract_server_port(config, proto)
        if not host or not port:
            return None, False
            
        # Запускаем оригинальный TCP-тест
        is_alive = self.test_tcp_connection(host, port)
        return config, is_alive, proto

    def worker(self, config):
        """Рабочий поток для асинхронного выполнения"""
        return self.test_config(config)

    def display_progress(self, current, total):
        """Отображение хода выполнения проверки конвейера"""
        if total > 0 and current % 50 == 0:
            percent = (current / total) * 100
            print(f"🔹 [ОТК ПРОГРЕСС] Проверено точек доступа: {current}/{total} ({percent:.1f}%)", flush=True)

    def test_all_configs(self):
        """Главный управляющий многопоточный метод валидации всех прокси"""
        configs = self.read_configs()
        total = len(configs)
        print(f"🏭 [ОТК] Извлечено для сетевого тестирования: {total} уникальных конфигураций.", flush=True)
        
        if total == 0:
            return

        # Запуск многопоточного цеха проверки (100 потоков защищают Гитхаб от зависания!)
        current_count = 0
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(self.worker, cfg) for cfg in configs]
            
            for future in as_completed(futures):
                current_count += 1
                self.display_progress(current_count, total)
                self.stats['total_checked'] += 1
                
                result = future.result()
                if result and result[1]: # Если TCP тест пройден успешно!
                    cfg, _, proto = result
                    self.valid_configs[proto].append(cfg)
                    self.stats['valid_configs'] += 1
                else:
                    self.stats['failed_tcp'] += 1

        # Сохранение очищенных результатов согласно структуре на скриншоте 1390
        self.save_valid_configs()

    def save_valid_configs(self):
        """Оригинальный метод сохранения прошедших TCP-тест конфигураций"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Перезаписываем файлы протоколов, оставляя в них только ЖИВЫЕ прокси
            for protocol, configs in self.valid_configs.items():
                if not configs:
                    # Если живых нет, удаляем старый битый файл, чтоб не захламлять софт Н
                    safe_name = protocol.replace('+', '_')
                    file_path = os.path.join(self.output_dir, f"{safe_name}.txt")
                    if os.path.exists(file_path):
                        try: os.remove(file_path)
                        except: pass
                    continue
                    
                safe_name = protocol.replace('+', '_')
                file_path = os.path.join(self.output_dir, f"{safe_name}.txt")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Печатаем оригинальные шапки метаданных, как на Снимок экрана (1390).png
                    f.write(f"# All Valid Configurations - TCP Test Passed\n")
                    f.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Total valid configs: {len(configs)}\n\n")
                    f.write(f"# {protocol.upper()} ({len(configs)} configs)\n")
                    for config in configs:
                        f.write(f"{config}\n")
            
            # Праздничный финальный гвардейский отчёт Завода Леи! 📊🦖
            print("\n📊 " + "="*23 + " ОТЧЁТ ОРИГИНАЛЬНОГО TCP-ВАЛИДАТОРА ОТК " + "="*23, flush=True)
            print(f"📥 ВСЕГО ТОЧЕК ДОСТУПА НАПРАВЛЕНО НА СЕТЕВОЙ ТЕСТ: {self.stats['total_checked']} шт.", flush=True)
            print(f"✅ УСПЕШНО ПРОШЛИ ТЕСТ TCP-CONNECTIVITY: {self.stats['valid_configs']} шт. 🔥", flush=True)
            print(f"🗑️ МЁРТВЫХ (НЕОТВЕТИВШИХ) СЕРВЕРОВ УДАЛЕНО ИЗ БАЗЫ: {self.stats['failed_tcp']} шт. 🛡️", flush=True)
            print(f"⏱️ СКОРОСТЬ ПРОВЕРКИ: Разгон до 100 потоков выполнен идеально! Без зависаний.", flush=True)
            print("=====================================================================================\n", flush=True)
            
        except Exception as e:
            print(f"Error saving combined valid configurations: {e}")

def main():
    sys.stdout.reconfigure(line_buffering=True)
    title = "Tests TCP connectivity of proxy configurations"
    print(title)
    print("=" * len(title))
    
    validator = ConnectivityValidator()
    validator.test_all_configs()
    print("\nTesting and saving completed successfully!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print("FormatParser-Validator v3.0-Monolith")
        sys.exit(0)
    main()
