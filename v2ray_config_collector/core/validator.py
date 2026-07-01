import os
import re
import sys
import time
import json
import base64
import asyncio
import urllib.parse
from datetime import datetime

class ConnectivityValidator:
    def __init__(self, input_file=None):
        current_file_path = os.path.abspath(__file__)
        core_dir = os.path.dirname(current_file_path)          
        project_dir = os.path.dirname(core_dir)                
        self.base_dir = os.path.dirname(project_dir)           

        self.input_file = input_file
        
        self.chunk_label = "Общий поток"
        if self.input_file:
            self.chunk_label = os.path.splitext(os.path.basename(self.input_file))[0].upper()

        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique') 
        
        self.protocols = [
            'naive+https', 'shadowtls', 'trusttunnel', 'hysteria2', 'wireguard', 
            'juicity', 'socks5', 'socks4', 'anytls', 'vmess', 'vless', 'trojan', 
            'naive', 'socks', 'https', 'http', 'tuic', 'hy2', 'ssh', 'wg', 'ss'
        ]

        self.valid_configs = {proto: [] for proto in self.protocols}
        self.valid_configs['clash'] = [] 
        
        self.lock = asyncio.Lock()
        self.stats = {'valid_configs': 0, 'total_checked': 0, 'failed_tcp': 0}

    def read_configs(self):
        all_lines = []
        if self.input_file and os.path.exists(self.input_file):
            try:
                with open(self.input_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line_clean = line.strip()
                        if line_clean and not line_clean.startswith('#'):
                            all_lines.append(line_clean)
            except:
                pass
            return list(set(all_lines))

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
        if config.startswith('clash-config://'):
            return 'clash'
            
        config_lower = config.lower()
        if config_lower.startswith('http://') or config_lower.startswith('https://'):
            try:
                parsed = urllib.parse.urlparse(config)
                path_clean = parsed.path.strip('/')
                if path_clean or not parsed.port:
                    if not any(k in config_lower for k in ['key=', 'sub', 'token=', 'clash', '.txt', '.yaml', '.conf']):
                        return None
            except:
                return None

        for proto in self.protocols:
            if config.lower().startswith(f"{proto}://"):
                return proto
        return None

    def extract_server_port(self, config, protocol):
        try:
            if protocol == 'clash':
                b64_str = config.split('://')[1]
                dec = base64.b64decode(b64_str).decode('utf-8')
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

    async def test_tcp_connection(self, host, port, timeout=4.0):
        if not host or not port:
            return False
        try:
            conn = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(conn, timeout=timeout)
            writer.close()
            try:
                await writer.wait_closed()
            except:
                pass
            return True 
        except:
            return False

    def display_progress(self, current, total):
        if total > 0 and current % 500 == 0:
            percent = (current / total) * 100
            print(f"🔹 [ОТК ПРОГРЕСС] [{self.chunk_label}] Проверено: {current}/{total} ({percent:.1f}%)", flush=True)

    async def worker(self, queue, total):
        while not queue.empty():
            try:
                cfg = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            proto = self.detect_protocol(cfg)
            if not proto:
                queue.task_done()
                async with self.lock:
                    self.stats['total_checked'] += 1
                    self.stats['failed_tcp'] += 1
                continue

            host, port = self.extract_server_port(cfg, proto)
            if not host or not port:
                queue.task_done()
                async with self.lock:
                    self.stats['total_checked'] += 1
                    self.stats['failed_tcp'] += 1
                continue

            is_alive = await self.test_tcp_connection(host, port)

            async with self.lock:
                self.stats['total_checked'] += 1
                if is_alive:
                    self.valid_configs[proto].append(cfg)
                    self.stats['valid_configs'] += 1
                else:
                    self.stats['failed_tcp'] += 1
                
                self.display_progress(self.stats['total_checked'], total)

            queue.task_done()

    async def run_validation(self, configs):
        total = len(configs)
        queue = asyncio.Queue()
        
        for cfg in configs:
            queue.put_nowait(cfg)

        num_workers = min(800, total)
        workers = [
            asyncio.create_task(self.worker(queue, total)) 
            for _ in range(num_workers)
        ]

        await asyncio.gather(*workers)

    def test_all_configs(self):
        configs = self.read_configs()
        total = len(configs)
        print(f"🏭 [ОТК] [{self.chunk_label}] Извлечено для теста: {total} configurations.", flush=True)
        if total == 0:
            return

        asyncio.run(self.run_validation(configs))
        self.save_valid_configs()

    def save_valid_configs(self):
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            
            suffix = ""
            if self.input_file:
                chunk_name = os.path.splitext(os.path.basename(self.input_file))[0]
                suffix = f"_{chunk_name}"

            for protocol, configs in self.valid_configs.items():
                if not configs:
                    continue
                    
                safe_name = protocol.replace('+', '_')
                file_path = os.path.join(self.output_dir, f"{safe_name}{suffix}.txt")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# All Valid Configurations - TCP Test Passed\n")
                    f.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Total valid configs: {len(configs)}\n\n")
                    f.write(f"# {protocol.upper()} ({len(configs)} configs)\n")
                    
                    # ИСПРАВЛЕНО НАВСЕГДА: Построчный перебор списка
                    for config in configs:
                        f.write(f"{config}\n")
            
            print(f"\n📊 ================= ОТЧЁТ TCP-ВАЛИДАТОРА [{self.chunk_label}] =================", flush=True)
            print(f"📥 ВСЕГО ТОЧЕК ДОСТУПА В КУСКЕ: {self.stats['total_checked']} шт.", flush=True)
            print(f"✅ УСПЕШНО ПРОШЛИ ТЕСТ: {self.stats['valid_configs']} шт. 🔥", flush=True)
            print(f"🗑️ МЁРТВЫХ СЕРВЕРОВ УДАЛЕНО: {self.stats['failed_tcp']} шт. 🛡️", flush=True)
            print("=====================================================================================\n", flush=True)
            
        except Exception as e:
            print(f"Error saving combined valid configurations: {e}")

def main():
    sys.stdout.reconfigure(line_buffering=True)
    
    input_file = None
    if "--input" in sys.argv:
        idx = sys.argv.index("--input")
        if idx + 1 < len(sys.argv):
            input_file = sys.argv[idx + 1]
    
    validator = ConnectivityValidator(input_file=input_file)
    validator.test_all_configs()
    print("\nTesting and saving completed successfully!")

if __name__ == "__main__":
    main()
