import os
import socket
import sys
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class ConnectivityValidator:
    def __init__(self):
        # Автоматически определяем пути относительно папки core
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_file = os.path.join(self.base_dir, 'data', 'raw', 'raw_configs.txt')
        self.output_file = os.path.join(self.base_dir, 'data', 'validated', 'validated_configs.txt')
        
        self.timeout = 4  # 4 секунды — золотая середина
        self.max_workers = 100 # Скорость для настоящего Главы Семьи

    def parse_address(self, config):
        """Парсим адрес для проверки TCP соединения"""
        try:
            config = config.strip()
            # Убираем протокол для корректного парсинга netloc
            if "://" in config:
                parsed = urlparse(config)
                netloc = parsed.netloc
            else:
                netloc = config

            if '@' in netloc:
                address = netloc.split('@')[1]
            else:
                address = netloc
            
            # Очистка от мусора в конце (имена, параметры)
            address = address.split('?')[0].split('#')[0]
            
            if ':' in address:
                host, port = address.rsplit(':', 1)
                return host, int(port)
        except Exception:
            pass
        return None, None

    def check_tcp(self, config):
        """Стучимся в порт. Если ответил — узел живой!"""
        host, port = self.parse_address(config)
        if not host or not port:
            return None
        try:
            # Пытаемся создать соединение
            with socket.create_connection((host, port), timeout=self.timeout):
                return config
        except Exception:
            return None

    def test_all_configs(self):
        print(f"\n⚖️ [VALIDATOR] Начинаю проверку узлов на прочность...")
        
        if not os.path.exists(self.input_file):
            print(f"❌ Файл для проверки не найден: {self.input_file}")
            return

        # Читаем уникальные конфиги
        with open(self.input_file, 'r', encoding='utf-8') as f:
            configs = list(set([line.strip() for line in f if line.strip()]))

        if not configs:
            print("📭 Нечего проверять, файл пуст.")
            return

        print(f"📡 Всего на проверку: {len(configs)} узлов.")
        
        valid_configs = []
        
        # Используем ThreadPoolExecutor для многопоточности
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # tqdm создаст ту самую полоску прогресса, которую ты любишь
            results = list(tqdm(executor.map(self.check_tcp, configs), 
                                total=len(configs), 
                                desc="Проверка портов",
                                leave=True))
            
        valid_configs = [r for r in results if r is not None]

        # Сохраняем результат
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(valid_configs))
        
        print(f"✅ ВАЛИДАЦИЯ ЗАВЕРШЕНА!")
        print(f"🏆 Живых серверов найдено: {len(valid_configs)}")
        print(f"📂 Результат в: {self.output_file} 💋💍")
