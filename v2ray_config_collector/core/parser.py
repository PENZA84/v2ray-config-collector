import os
import re

try:
    import yaml
    YAML_READY = True
except ImportError:
    YAML_READY = False

class FormatConverter:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Откуда берем сырье
        self.input_dir = os.path.join(self.base_dir, 'data', 'raw')
        
        # КУДА КЛАДЕМ (Исправила на unique, чтобы Валидатор увидел!)
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        
        self.output_file = os.path.join(self.output_dir, 'deduplicated.txt')
        self.dns_file = os.path.join(self.output_dir, 'dns_list.txt')

    def extract_from_yaml(self, content):
        """Парсинг Clash YAML"""
        if not YAML_READY:
            return []
        extracted = []
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict) and 'proxies' in data:
                for p in data['proxies']:
                    t = p.get('type', '').lower()
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password')
                    name = p.get('name', 'clash').replace(' ', '_')
                    
                    if all([t, server, port, uuid]):
                        link = f"{t}://{uuid}@{server}:{port}#{name}"
                        extracted.append(link)
        except:
            pass 
        return extracted

    def process(self):
        print(f"🛠 [PARSER] Глубокая переработка сырья в unique...")
        
        if not os.path.exists(self.input_dir):
            print("📭 Папка raw пуста. Сначала запусти Fetcher или main1.py!")
            return

        configs = []
        dns_ips = set()
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        proto_pattern = r'(?:vless|vmess|ss|trojan|tuic|hysteria2|hy2|juicity|naive|shadowtls)://[^\s|\"|\'|<]+'

        for filename in os.listdir(self.input_dir):
            file_path = os.path.join(self.input_dir, filename)
            if filename in ['deduplicated.txt', 'dns_list.txt']: continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    configs.extend(re.findall(proto_pattern, content, re.IGNORECASE))
                    if 'proxies:' in content:
                        configs.extend(self.extract_from_yaml(content))
                    dns_ips.update(ip_pattern.findall(content))
            except Exception as e:
                print(f"⚠️ Ошибка в {filename}: {e}")

        # Сохраняем результат там, где его ждет Валидатор
        os.makedirs(self.output_dir, exist_ok=True)
        configs = sorted(list(set(configs))) # Чистим дубли и сортируем
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(configs))
        with open(self.dns_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(list(dns_ips)))

        print(f"✅ Готово! В папку /unique/ сохранено {len(configs)} конфигов. 💋")
