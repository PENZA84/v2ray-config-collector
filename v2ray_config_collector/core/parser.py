import base64
import json
import urllib.parse
import os

class FormatConverter:
    def __init__(self, input_files=None, output_file=None):
        # Настройка путей строго под твою структуру папок
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_files = input_files or [os.path.join(package_dir, 'data', 'raw', 'raw_configs.txt')]
        self.output_file = output_file or os.path.join(package_dir, 'data', 'unique', 'deduplicated.txt')
        self.stats = {'total': 0, 'success': 0, 'failed': 0}

    def detect_protocol(self, line):
        line = line.lower().strip()
        protocols = ['vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://', 'tuic://', 'hysteria2://', 'hy2://', 'hysteria://', 'socks5://', 'socks4://', 'http://', 'https://']
        for proto in protocols:
            if line.startswith(proto):
                return proto.replace('://', '')
        return 'unknown'

    def convert_configs(self):
        """ЭТОТ МЕТОД ВЫЗЫВАЕТ ТВОЙ MAIN.PY — ТЕПЕРЬ ОНИ СВЯЗАНЫ НАВЕК"""
        all_configs = []
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        for file_path in self.input_files:
            if not os.path.exists(file_path):
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    self.stats['total'] += 1
                    if self.detect_protocol(line) != 'unknown':
                        all_configs.append(line)
                        self.stats['success'] += 1
                    else:
                        self.stats['failed'] += 1

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_configs))
        print(f"Парсер отработал: {self.stats['success']} конфигов готово для дедупликатора.")
