import os
import socket
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class ConnectivityValidator:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.timeout = 4  # Дорогой, 4 секунды — это идеально, чтобы не ждать мертвецов
        self.max_workers = 100 # Высокая скорость для твоих объемов

    def parse_address(self, config):
        """Парсим адрес, чтобы проверить, живой ли сервер."""
        try:
            config = config.strip()
            parsed = urlparse(config)
            netloc = parsed.netloc
            if '@' in netloc:
                address = netloc.split('@')[1]
            else:
                address = netloc
            if ':' in address:
                host_port = address.split('?')[0].split('#')[0]
                host, port = host_port.split(':')
                return host, int(port)
        except:
            pass
        return None, None

    def check_tcp(self, config):
        """Стучимся в порт. Если ответил — берем!"""
        host, port = self.parse_address(config)
        if not host or not port:
            return None
        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                return config
        except:
            return None

    def test_all_configs(self):
        if not os.path.exists(self.input_file):
            return

        with open(self.input_file, 'r', encoding='utf-8') as f:
            configs = list(set([line.strip() for line in f if line.strip()]))

        if not configs:
            return

        print(f"📡 Проверяю {len(configs)} узлов. Начинаю чистку...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(tqdm(executor.map(self.check_tcp, configs), total=len(configs), desc="Валидация"))
            
        valid_configs = [r for r in results if r is not None]

        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(valid_configs))
        
        print(f"✅ Готово! Живых: {len(valid_configs)}")
