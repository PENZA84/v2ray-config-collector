import socket
import os
import threading
import queue
import base64
import json

class ConnectivityValidator:
    def __init__(self, input_file=None, output_dir=None):
        # Определяем пути относительно корня проекта
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_file = input_file or os.path.join(package_dir, 'data', 'unique', 'deduplicated.txt')
        self.output_dir = output_dir or os.path.join(package_dir, 'data', 'validated')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.valid_configs = [] 
        self.max_workers = 100
        self.timeout = 5
        self.queue = queue.Queue()
        self.lock = threading.Lock()

    def extract_server_port(self, url):
        try:
            url_lower = url.lower()
            if url_lower.startswith('vmess://'):
                data = json.loads(base64.b64decode(url.replace("vmess://", "")).decode('utf-8'))
                return data.get('add'), int(data.get('port', 443))
            
            # Парсинг для vless, trojan, ss, socks, http и прочих для Sing-box
            addr = url.split('://', 1)[1].split('#')[0].split('?')[0]
            if '@' in addr: addr = addr.split('@', 1)[1]
            
            if ':' in addr:
                if ']' in addr: # IPv6
                    host = addr.split(']')[0] + ']'
                    port = addr.split(']')[-1].replace(':', '').split('/')[0]
                else:
                    host, port = addr.split(':', 1)
                    port = port.split('/')[0]
                return host.strip(), int(port)
            return addr.split('/')[0].strip(), 443
        except:
            return None, None

    def test_worker(self):
        while not self.queue.empty():
            try:
                url = self.queue.get_nowait()
                host, port = self.extract_server_port(url)
                if host and port:
                    try:
                        # Проверка доступности порта (TCP Check)
                        with socket.create_connection((host, port), timeout=self.timeout):
                            with self.lock:
                                self.valid_configs.append(url)
                    except: pass
                self.queue.task_done()
            except queue.Empty: break

    def test_all_configs(self):
        """Метод, который вызывает твой main.py"""
        if not os.path.exists(self.input_file):
            print(f"Файл не найден: {self.input_file}")
            return

        with open(self.input_file, 'r', encoding='utf-8') as f:
            configs = [l.strip() for l in f if l.strip() and not l.strip().startswith('#')]
        
        for c in configs: self.queue.put(c)
        
        print(f"Проверяю {len(configs)} конфигов...")
        threads = []
        for _ in range(min(self.max_workers, len(configs))):
            t = threading.Thread(target=self.test_worker, daemon=True)
            t.start()
            threads.append(t)
        
        for t in threads: t.join()
        
        # Сохраняем ТОЛЬКО один файл all_valid.txt
        out_path = os.path.join(self.output_dir, "all_valid.txt")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.valid_configs))
            
        print(f"Готово! Рабочие прокси сохранены в {out_path}")
