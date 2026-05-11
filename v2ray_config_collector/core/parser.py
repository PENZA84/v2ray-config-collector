import os
import re
import json
import base64
import yaml
import urllib.parse

class FormatConverter:
    def __init__(self, input_files=None, output_dir=None):
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_files = input_files or [os.path.join(package_dir, 'data', 'raw', 'raw_configs.txt')]
        self.output_dir = output_dir or os.path.join(package_dir, 'data', 'unique')
        self.output_file = os.path.join(self.output_dir, 'deduplicated.txt')
        self.dns_file = os.path.join(self.output_dir, 'dns_list.txt')
        
        self.stats = {
            'proxies': 0,
            'yaml_collected': 0,
            'b64_decoded': 0,
            'dns_found': 0
        }

    def construct_vless(self, p):
        """Сборка VLESS из словаря (Clash формат)"""
        try:
            uuid = p.get('uuid')
            server = p.get('server')
            port = p.get('port')
            if not all([uuid, server, port]): return None
            
            params = {
                'type': p.get('network', 'tcp'),
                'security': 'tls' if p.get('tls') or p.get('udp') else 'none',
                'sni': p.get('servername', p.get('sni', '')),
                'fp': p.get('client-fingerprint', ''),
                'path': p.get('ws-opts', {}).get('path', '') if p.get('network') == 'ws' else ''
            }
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
            name = urllib.parse.quote(p.get('name', 'Clash_Node'))
            return f"vless://{uuid}@{server}:{port}?{query}#{name}"
        except: return None

    def try_base64_decode(self, text):
        """Декодер для подписок"""
        try:
            text = text.strip()
            if len(text) < 20: return None
            missing_padding = len(text) % 4
            if missing_padding: text += '=' * (4 - missing_padding)
            decoded = base64.b64decode(text).decode('utf-8')
            if "://" in decoded or "proxies:" in decoded or "{" in decoded:
                self.stats['b64_decoded'] += 1
                return decoded
        except: pass
        return None

    def extract_all(self, content):
        """Парсит всё: ссылки, YAML прокси и DNS IP"""
        found_proxies = set()
        found_dns = set()

        # 1. Поиск готовых ссылок (Regex)
        links = re.findall(r'(vmess|vless|trojan|ss|ssr|tuic|hy2|hysteria2)://[^\s"\'}]+', content)
        found_proxies.update(links)

        # 2. Глубокий анализ структур (YAML/JSON)
        if "proxies:" in content or "dns:" in content or '"server"' in content:
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    # Ищем прокси (Clash/Sing-box)
                    nodes = data.get('proxies', []) or data.get('outbounds', [])
                    if isinstance(nodes, list):
                        for n in nodes:
                            if not isinstance(n, dict): continue
                            if n.get('type') == 'vless':
                                link = self.construct_vless(n)
                                if link: 
                                    found_proxies.add(link)
                                    self.stats['yaml_collected'] += 1
                    
                    # Ищем DNS (те самые цифры-примеры)
                    dns_section = data.get('dns', {})
                    if isinstance(dns_section, dict):
                        for key in ['nameserver', 'fallback', 'default-nameserver']:
                            servers = dns_section.get(key, [])
                            if isinstance(servers, list):
                                for s in servers:
                                    # Регулярка для проверки IP адреса
                                    if isinstance(s, str) and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', s):
                                        found_dns.add(s)
            except: pass
        
        return found_proxies, found_dns

    def process(self):
        all_proxies = set()
        all_dns = set()
        os.makedirs(self.output_dir, exist_ok=True)

        for file_path in self.input_files:
            if not os.path.exists(file_path): continue
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Парсим как текст
                p, d = self.extract_all(content)
                all_proxies.update(p)
                all_dns.update(d)

                # Пробуем как Base64
                decoded = self.try_base64_decode(content)
                if decoded:
                    p, d = self.extract_all(decoded)
                    all_proxies.update(p)
                    all_dns.update(d)

        # Сохраняем прокси
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(sorted(list(all_proxies))))
        
        # Сохраняем DNS (в отдельный файл, чтобы не мусорить в прокси)
        if all_dns:
            with open(self.dns_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(sorted(list(all_dns))))
            self.stats['dns_found'] = len(all_dns)

        print(f"✅ ПАРСИНГ ЗАВЕРШЕН:")
        print(f"   - Уникальных прокси: {len(all_proxies)}")
        print(f"   - Собрано из YAML:    {self.stats['yaml_collected']}")
        print(f"   - Найдено DNS (IP):  {self.stats['dns_found']}")
        if self.stats['dns_found'] > 0:
            print(f"   - Файл с DNS: {self.dns_file}")

if __name__ == "__main__":
    FormatConverter().process()
