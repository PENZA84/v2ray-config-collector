import os
import re
import yaml # Дорогой, если библиотеки нет, напиши pip install pyyaml

class FormatConverter:
    def __init__(self, input_files, output_dir):
        self.input_files = input_files
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, 'deduplicated.txt')
        self.dns_file = os.path.join(output_dir, 'dns_list.txt')

    def extract_from_yaml(self, content):
        """Парсим Clash YAML (как на скрине 925)"""
        extracted = []
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict) and 'proxies' in data:
                for p in data['proxies']:
                    # Собираем ссылку вручную из полей YAML
                    t = p.get('type', '').lower()
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password')
                    name = p.get('name', 'clash_proxy').replace(' ', '_')
                    
                    if all([t, server, port, uuid]):
                        # Формируем стандартную ссылку (базовый пример)
                        link = f"{t}://{uuid}@{server}:{port}#{name}"
                        extracted.append(link)
        except:
            pass # Если не YAML, просто идем дальше
        return extracted

    def process(self):
        configs = []
        dns_ips = set()
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        
        # РАСШИРЕННЫЙ СПИСОК ПРОТОКОЛОВ (все твои!)
        proto_pattern = r'(?:vless|vmess|ss|trojan|tuic|hysteria2|hy2|juicity|naive|shadowtls)://[^\s|\"|\'|<]+'

        for file_path in self.input_files:
            if not os.path.exists(file_path):
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 1. Ищем стандартные ссылки
                found = re.findall(proto_pattern, content, re.IGNORECASE)
                configs.extend(found)
                
                # 2. Пробуем вытащить из YAML (Clash)
                yaml_configs = self.extract_from_yaml(content)
                configs.extend(yaml_configs)
                
                # 3. Собираем IP
                dns_ips.update(ip_pattern.findall(content))

        os.makedirs(self.output_dir, exist_ok=True)
        # Убираем дубликаты сразу
        configs = list(set(configs))
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(configs))
        with open(self.dns_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(list(dns_ips)))

        print(f"📦 Парсинг завершен: {len(configs)} конфигов (включая YAML и новые протоколы).")
