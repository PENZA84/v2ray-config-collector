import os
import re
import yaml
import base64
import urllib.parse

class FormatConverter:
    def __init__(self, input_files=None, output_dir=None):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_files = input_files or [os.path.join(base_path, 'data', 'raw', 'raw_configs.txt')]
        self.output_dir = output_dir or os.path.join(base_path, 'data', 'unique')
        self.output_file = os.path.join(self.output_dir, 'deduplicated.txt')
        self.dns_file = os.path.join(self.output_dir, 'dns_list.txt')
        self.stats = {'total_links': 0, 'dns': 0}

    def extract_logic(self, text):
        proxies, dns = set(), set()
        # 1. Стандартные ссылки
        proxies.update(re.findall(r'(vmess|vless|trojan|ss|ssr|tuic|hy2)://[^\s"\'}]+', text))
        
        # 2. Поиск DNS (любые IP 4-ки, которые выглядят как DNS в конфигах)
        found_ips = re.findall(r'(?<=[:\-\s])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?=\s|$|\n)', text)
        for ip in found_ips:
            if not ip.startswith(('127.', '192.168.', '10.', '0.')): # Исключаем локалки
                dns.add(ip)
        
        # 3. Попытка распарсить YAML даже если он битый
        try:
            data = yaml.safe_load(text)
            if isinstance(data, dict):
                # Ищем прокси в любых ключах, где есть списки
                for key in ['proxies', 'outbounds', 'nodes']:
                    items = data.get(key, [])
                    if isinstance(items, list):
                        for n in items:
                            if isinstance(n, dict) and n.get('server'):
                                # Собираем простую ссылку для теста
                                proxies.add(f"vless://{n.get('uuid', 'id')}@{n.get('server')}:{n.get('port', 443)}?type={n.get('network', 'tcp')}#Imported")
        except: pass
        return proxies, dns

    def process(self):
        all_p, all_d = set(), set()
        os.makedirs(self.output_dir, exist_ok=True)
        
        if not os.path.exists(self.input_files[0]): return

        with open(self.input_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Сначала пробуем Base64 (весь файл)
            try:
                decoded = base64.b64decode(content).decode('utf-8')
                p, d = self.extract_logic(decoded)
                all_p.update(p); all_d.update(d)
            except: pass
            
            # Затем парсим как обычный текст
            p, d = self.extract_logic(content)
            all_p.update(p); all_d.update(d)

        with open(self.output_file, 'w') as f: f.write("\n".join(all_p))
        if all_d:
            with open(self.dns_file, 'w') as f: f.write("\n".join(all_d))
        
        print(f"✅ Найдено потенциальных прокси: {len(all_p)}")
        print(f"✅ Найдено IP (DNS): {len(all_d)}")

if __name__ == "__main__":
    FormatConverter().process()
