import os
import socket
import sys
import re
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class ConnectivityValidator:
    def __init__(self):
        # Автоматические пути — синхронизируем с Парсером
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Важно: берем файл deduplicated.txt, который создал наш новый Парсер
        self.input_file = os.path.join(self.base_dir, 'data', 'raw', 'deduplicated.txt')
        self.output_file = os.path.join(self.base_dir, 'data', 'validated', 'validated_configs.txt')
        
        self.timeout = 4  
        self.max_workers = 100 

    def parse_address(self, config):
        """Улучшенный парсер: понимает сложные ссылки из YAML и прокси-листов"""
        try:
            config = config.strip()
            # 1. Обработка протокола
            if "://" in config:
                # Специально для сложных ссылок с кучей параметров после # или ?
                # Убираем всё после решетки, чтобы не мешало парсить хост
                clean_config = config.split('#')[0]
                parsed = urlparse(clean_config)
                netloc = parsed.netloc
            else:
                netloc = config

            # 2. Очистка от авторизации (user:pass@host:port)
            if '@' in netloc:
                address = netloc.rsplit('@', 1)[1]
            else:
                address = netloc
            
            # 3. Финальная чистка хоста от параметров запроса
            address = address.split('?')[0].split('/')[0]
            
            # 4. Выделение Хоста и Порта
            if ':' in address:
                # Используем rsplit, чтобы правильно обработать IPv6
                host, port = address.rsplit(':', 1)
                # Убираем квадратные скобки из IPv6 если они есть
                host = host.strip('[]')
                return host, int(port)
        except Exception:
            pass
        return None, None

    def check_tcp(self, config):
        """Стучимся в дверь сервера. Если открыто — забираем в базу."""
        host, port = self.parse_address(config)
        if not host or not port:
            return None
        try:
            # create_connection — самый надежный способ проверить "живучесть" порта
            with socket.create_connection((host, port), timeout=self.timeout):
                return config
        except Exception:
            return None

    def test_all_configs(self):
        print(f"\n⚖️ [VALIDATOR] Цех проверки запущен...")
        
        if not os.path.exists(self.input_file):
            print(f"❌ ОШИБКА: Файл {self.input_file} не найден. Сначала запусти Парсер!")
            return

        # Читаем то, что подготовил Парсер
        with open(self.input_file, 'r', encoding='utf-8') as f:
            configs = list(set([line.strip() for line in f if line.strip()]))

        if not configs:
            print("📭 Список для проверки пуст. Ждем новых поставок!")
            return

        print(f"📡 Всего на проверку (включая YAML-добычу): {len(configs)} узлов.")
        
        # Запускаем многопоточный сканер
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # tqdm показывает живой прогресс в логах Гитхаба
            results = list(tqdm(executor.map(self.check_tcp, configs), 
                                total=len(configs), 
                                desc="Проверка соединений",
                                leave=True))
            
        valid_configs = [r for r in results if r is not None]

        # Сохраняем в папку валидированных данных
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(valid_configs))
        
        print(f"✅ ВАЛИДАЦИЯ ЗАВЕРШЕНА!")
        print(f"🏆 Живых серверов для твоей семьи: {len(valid_configs)}")
        print(f"📂 Результат бережно сохранен в: {self.output_file} 💋💍")
