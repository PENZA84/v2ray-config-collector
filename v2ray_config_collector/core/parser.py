import os
import re
import base64
import yaml
import urllib.parse

class FormatConverter:
    def __init__(self, input_files=None, output_dir=None):
        # Автоматическое определение базовой директории проекта
        # Находим путь к v2ray_config_collector (корень проекта)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.input_files = input_files or [os.path.join(base_path, 'data', 'raw', 'raw_configs.txt')]
        self.output_dir = output_dir or os.path.join(base_path, 'data', 'unique')
        self.output_file = os.path.join(self.output_dir, 'deduplicated.txt')
        self.dns_file = os.path.join(self.output_dir, 'dns_list.txt')
        
        self.stats = {'yaml_collected': 0, 'b64_decoded': 0, 'dns_found': 0}

    def construct_vless(self, p):
        try:
            uuid, server, port = p.get('uuid'), p.get('server'), p.get('port')
            if not all([uuid, server, port]): return None
            params = {
                'type': p.get('network', 'tcp'),
                'security': 'tls' if p.get('tls') else 'none',
                'sni': p.get('servername', p.get('sni', '')),
                'path': p.get('ws-opts', {}).get('path', '') if p.get('network') == 'ws' else ''
            }
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
            return f"vless://{uuid}@{server}:{port}?{query}#{urllib.parse.quote(p.get('name', 'Node'))}"
        except: return None

    def extract_all(self, content):
        proxies, dns = set(), set()
        # Готовые ссылки
        proxies.update(re.findall(r'(vmess|vless|trojan|ss|ssr|tuic|hy2|hysteria2)://[^\s"\'}]+', content))
        # YAML/JSON структуры
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                nodes = data.get('proxies', []) or data.get('outbounds', [])
                if isinstance(nodes, list):
                    for n in nodes:
                        if isinstance(n, dict) and n.get('type') == 'vless':
                            link = self.construct_vless(n)
                            if link: proxies.add(link); self.stats['yaml_collected'] += 1
                # Сбор DNS
                dns_sec = data.get('dns', {})
                if isinstance(dns_sec, dict):
                    for k in ['nameserver', 'fallback', 'default-nameserver']:
                        for s in dns_sec.get(k, []):
                            if isinstance(s, str) and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', s):
                                dns.add(s)
        except: pass
        return proxies, dns

    def process(self):
        all_p, all_d = set(), set()
        os.makedirs(self.output_dir, exist_ok=True)

        for f_path in self.input_files:
            if not os.path.exists(f_path): continue
            with open(f_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Как текст
                p, d = self.extract_all(content)
                all_p.update(p); all_d.update(d)
                # Как Base64
                try:
                    missing_padding = len(content.strip()) % 4
                    decoded = base64.b64decode(content.strip() + '=' * (4 - missing_padding)).decode('utf-8')
                    if any(x in decoded for x in ["://", "proxies:", "{"]):
                        p, d = self.extract_all(decoded)
                        all_p.update(p); all_d.update(d); self.stats['b64_decoded'] += 1
                except: pass

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(sorted(list(all_p))))
        
        if all_d:
            with open(self.dns_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(sorted(list(all_d))))
            self.stats['dns_found'] = len(all_d)

        print(f"✅ Parser: {len(all_p)} proxies, {self.stats['dns_found']} DNS.")

if __name__ == "__main__":
    FormatConverter().process()
