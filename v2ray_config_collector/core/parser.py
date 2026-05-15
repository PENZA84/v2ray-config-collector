import os
import re

# Пытаемся импортировать yaml, чтобы завод не встал, если библиотека еще ставится
try:
    import yaml
    YAML_READY = True
except ImportError:
    YAML_READY = False

class FormatConverter:
    def __init__(self):
        # Автоматически находим папки, чтобы тебе не вписывать их руками
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Собираем данные из всех сырых файлов, что накачал Фетчер
        self.input_dir = os.path.join(self.base_dir, 'data', 'raw')
        self.output_dir = os.path.join(self.base_dir, 'data', 'raw')
        
        self.output_file = os.path.join(self.output_dir, 'deduplicated.txt')
        self.dns_file = os.path.join(self.output_dir, 'dns_list.txt')

    def extract_from_yaml(self, content):
        """Твой метод парсинга Clash YAML (как на скрине 925)"""
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
                    name = p.get('name', 'clash_proxy').replace(' ', '_')
                    
                    if all([t, server, port, uuid]):
                        link = f"{t}://{uuid}@{server}:{port}#{name}"
                        extracted.append(link)
        except:
            pass 
        return extracted

    def process(self):
        """Основной цикл переработки сокровищ"""
        print(f"🛠 Парсер PENZA84: Начинаю глубокую переработку...")
        
        configs = []
        dns_ips = set()
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        
        # ТВОЙ РАСШИРЕННЫЙ СПИСОК (Берем всё!)
        proto_pattern = r'(?:vless|vmess|ss|trojan|tuic|hysteria2|hy2|juicity|naive|shadowtls)://[^\s|\"|\'|<]+'

        # Проходим по всем файлам в папке raw
        if not os.path.exists(self.input_dir):
            print("📭 Папка с сырыми данными пуста.")
            return

        for filename in os.listdir(self.input_dir):
            file_path = os.path.join(self.input_dir, filename)
            
            # Пропускаем наши же итоговые файлы, чтобы не зациклиться
            if filename in ['deduplicated.txt', 'dns_list.txt']: continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 1. Стандартные ссылки
                    found = re.findall(proto_pattern, content, re.IGNORECASE)
                    configs.extend(found)
                    
                    # 2. Clash YAML
                    if 'proxies:' in content:
                        configs.extend(self.extract_from_yaml(content))
                    
                    # 3. Собираем IP
                    dns_ips.update(ip_pattern.findall(content))
            except Exception as e:
                print(f"⚠️ Ошибка в файле {filename}: {e}")

        # Сохранение
        os.makedirs(self.output_dir, exist_ok=True)
        configs = list(set(configs)) # Удаляем дубликаты
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(configs))
            
        with open(self.dns_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(list(dns_ips)))

        print(f"✅ Готово! Собрано {len(configs)} конфигов и {len(dns_ips)} IP для DNS. 💋")
