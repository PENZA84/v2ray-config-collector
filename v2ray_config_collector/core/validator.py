import os
import re

class FormatConverter:
    def __init__(self, input_files, output_dir):
        self.input_files = input_files
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, 'deduplicated.txt')
        self.dns_file = os.path.join(output_dir, 'dns_list.txt')

    def process(self):
        configs = []
        dns_ips = set()
        
        # Регулярка для поиска IP (для DNS списка)
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

        for file_path in self.input_files:
            if not os.path.exists(file_path):
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Ищем конфиги (vless, vmess, ss, trojan)
                found = re.findall(r'(?:vless|vmess|ss|trojan)://[^\s|\"|\'|<]+', content)
                configs.extend(found)
                # Ищем IP для DNS
                dns_ips.update(ip_pattern.findall(content))

        os.makedirs(self.output_dir, exist_ok=True)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(configs))
            
        with open(self.dns_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(list(dns_ips)))

        print(f"📦 Парсинг завершен: {len(configs)} конфигов, {len(dns_ips)} IP для DNS.")
