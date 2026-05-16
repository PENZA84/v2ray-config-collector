import os
import socket
import sys
import re
import base64
import json
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class ConnectivityValidator:
    def __init__(self):
        # Автоматический корень: выходим из папки 'core' в корень репозитория GitHub
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Входной файл из папки unique, созданный Дедупликатором
        self.input_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')
        
        # Конечный склад — чистый путь, куда мы кладем живые уникальные протоколы
        self.output_file = os.path.join(self.base_dir, 'data', 'validated', 'validated_configs.txt')
        
        self.timeout = 4  
        self.max_workers = 100 
        
        # 🛡️ БАЗА ДЛЯ ЯДРА SING-BOX (Сюда сохраняем уникальные UUID / приватные ключи)
        self.seen_cores = set()

    def extract_sing_box_core_id(self, config_text):
        """
        🤖 ДВИЖОК ЯДРА SING-BOX: Выковыривает уникальный UUID или приватный ключ 
        из конфигурации, чтобы намертво срезать одинаковые прокси-серверы.
        """
        config_text = config_text.strip().replace('"', '').replace(',', '')
        try:
            # 1. Разбор VMESS (Декодируем Base64 и вытаскиваем уникальный "id" из ядра)
            if config_text.startswith("vmess://"):
                raw_b64 = config_text.replace("vmess://", "")
                raw_b64 += "=" * ((4 - len(raw_b64) % 4) % 4)  # Фикс паддинга Base64
                decoded_bytes = base64.b64decode(raw_b64)
                data_json = json.loads(decoded_bytes.decode('utf-8', errors='ignore'))
                return str(data_json.get("id", config_text))
                
            # 2. Разбор VLESS / TROJAN (Вырезаем UUID пользователя между // и @)
            elif config_text.startswith("vless://") or config_text.startswith("trojan://"):
                match = re.search(r'(?:vless|trojan)://([a-zA-Z0-9_\-\=]+)@', config_text)
                if match:
                    return match.group(1)
                    
            # 3. Разбор SHADOWSOCKS (Вырезаем уникальный зашифрованный ключ до @)
            elif config_text.startswith("ss://"):
                match = re.search(r'ss://([a-zA-Z0-9_\-\=\+]+)@', config_text)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return config_text  # Если протокол не распознан, сравниваем строку целиком

    def parse_address(self, config):
        """Парсер: понимает сложные ссылки из YAML и ТГ-каналов"""
        try:
            config = config.strip()
            if "://" in config:
                clean_config = config.split('#')[0]
                parsed = urlparse(clean_config)
                netloc = parsed.netloc
            else:
                netloc = config

            if '@' in netloc:
                address = netloc.rsplit('@', 1)[1]
            else:
                address = netloc
            
            address = address.split('?')[0].split('/')[0]
            
            if ':' in address:
                host, port = address.rsplit(':', 1)
                host = host.strip('[]')
                return host, int(port)
        except Exception:
            pass
        return None, None

    def check_tcp(self, config):
        """Проверка порта: быстро и надежно"""
        host, port = self.parse_address(config)
        if not host or not port:
            return None
        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                return config
        except Exception:
            return None

    def test_all_configs(self):
        print(f"\n⚖️ [VALIDATOR] Цех проверки портов запущен...")
        print("🛡️ Модуль фильтрации ядра Sing-Box [Vless/Vmess/SS/Trojan] успешно активирован.")
        
        # Проверка на существование файла
        if not os.path.exists(self.input_file):
            print(f"❌ ОШИБКА: Входной файл {self.input_file} не найден!")
            print(f"💡 Убедись, что Дедупликатор отработал и создал его.")
            return

        # Читаем данные из unique
        with open(self.input_file, 'r', encoding='utf-8') as f:
            raw_configs = [line.strip() for line in f if line.strip()]

        if not raw_configs:
            print("📭 В папке unique пусто. Нечего проверять.")
            return

        # 1. ПРИМЕНЕНИЕ ЯДРА SING-BOX: Вычищаем одинаковые прокси на входе
        unique_by_core = []
        duplicate_cores_count = 0
        
        for cfg in raw_configs:
            core_key = self.extract_sing_box_core_id(cfg)
            if core_key in self.seen_cores:
                duplicate_cores_count += 1
                continue  # Намертво отсекаем дубликат, не пингуя порт
            self.seen_cores.add(core_key)
            unique_by_core.append(cfg)

        print(f"📡 Всего загружено из unique: {len(raw_configs)} узлов.")
        print(f"🛡️ Движок Sing-Box вырезал дубликатов по UUID: {duplicate_cores_count} шт.")
        print(f"⚡ Отправлено на чекинг портов: {len(unique_by_core)} уникальных серверов.")
        
        # 2. Быстрая многопоточная проверка портов через ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(tqdm(executor.map(self.check_tcp, unique_by_core), 
                                total=len(unique_by_core), 
                                desc="Проверка портов",
                                leave=True))
            
        valid_configs = [r for r in results if r is not None]

        # Сохраняем результат строго по гитхаб-пути
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(valid_configs))
        
        print(f"\n==========================================================================")
        print(f"🏁 ГЛОБАЛЬНЫЙ ЗАВОД: ЦЕХ ВАЛИДАЦИИ ОТРАБОТАЛ УСПЕШНО!")
        print(f"🏆 Живых и уникальных серверов сохранено: {len(valid_configs)}")
        print(f"🛡️ Из базы вычищено дублей ядра Sing-Box: {duplicate_cores_count}")
        print(f"📂 Результат бережно сложен в: {self.output_file} 💋")
        print(f"==========================================================================")

if __name__ == "__main__":
    validator = ConnectivityValidator()
    validator.test_all_configs()
