import os
import socket
import sys
import re
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class ConnectivityValidator:
    def __init__(self):
        # Автоматические пути — синхронизируем с твоим новым складом
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 🎯 ВОТ ТУТ ИСПРАВИЛА: теперь смотрим в папку unique
        self.input_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')
        
        # Куда сохраняем живые прокси
        self.output_file = os.path.join(self.base_dir, 'data', 'validated', 'validated_configs.txt')
        
        self.timeout = 4  
        self.max_workers = 100 

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
        print(f"\n⚖️ [VALIDATOR] Цех проверки запущен (цель: папка unique)...")
        
        # Проверка на существование файла
        if not os.path.exists(self.input_file):
            print(f"❌ ОШИБКА: Файл {self.input_file} не найден!")
            print(f"💡 Убедись, что Дедупликатор отработал и создал его.")
            return

        # Читаем данные из unique
        with open(self.input_file, 'r', encoding='utf-8') as f:
            configs = list(set([line.strip() for line in f if line.strip()]))

        if not configs:
            print("📭 В папке unique пусто. Нечего проверять.")
            return

        print(f"📡 Всего на проверку: {len(configs)} узлов.")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
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
        print(f"🏆 Живых серверов для твоей семьи: {len(valid_configs)}")
        print(f"📂 Сохранено в: {self.output_file} 💋")
