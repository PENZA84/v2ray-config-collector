import os
import re
import requests
import yaml
import json
import base64
from urllib.parse import urlparse

class RawConfigsCollector:
    def __init__(self):
        # 📂 КОРЕНЬ ЗАВОДА
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Список RAW-ссылок (сюда зашиты как обычные TXT подписки, так и твои новые YAML источники)
        self.sources = [
            "https://raw.githubusercontent.com/asgharkapk/Sub-Config-Extractor/refs/heads/main/output_configs/clash/AzadNet/-t.me.yaml", # Твоя YAML ссылка!
            "https://raw.githubusercontent.com/w1770946466/Auto_Proxy/main/Long_term_subscription_num",
            "https://raw.githubusercontent.com/zu1k/proxypool/master/config/source.yaml" # Еще один популярный YAML-пул
        ]
        
        # Временный накопитель для сырых строк перед фильтрацией и нарезкой
        self.output_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')

    def parse_clash_yaml(self, yaml_text):
        """
        🧠 YAML-ДВИЖОК ДЛЯ RAW-ЦЕХА: Разбирает структуру Clash/Mihomo подписок.
        Превращает yaml-блоки в стандартные прокси-ссылки, которые понимает v2rayN («H») и Трон.
        """
        extracted_proxies = []
        try:
            # Безопасно загружаем структуру данных из YAML
            data = yaml.safe_load(yaml_text)
            if not data or not isinstance(data, dict) or 'proxies' not in data:
                return extracted_proxies

            for p in data['proxies']:
                try:
                    p_type = str(p.get('type', '')).lower()
                    name = p.get('name', 'RAW_YAML_Proxy').replace(' ', '_')
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password') # Для VMess/VLESS/Trojan/Shadowsocks
                    
                    if not server or not port:
                        continue

                    # 1. Парсинг VLESS из структуры YAML
                    if p_type == 'vless':
                        link = f"vless://{uuid}@{server}:{port}?type={p.get('network', 'tcp')}"
                        if p.get('tls'): link += "&security=tls"
                        if p.get('reality-opts') or p.get('reality'): link += "&security=reality"
                        link += f"#{name}"
                        extracted_proxies.append(link)

                    # 2. Парсинг VMESS из структуры YAML
                    elif p_type == 'vmess':
                        v_json = {
                            "v": "2", "ps": name, "add": server, "port": str(port),
                            "id": uuid, "aid": "0", "net": p.get('network', 'tcp'),
                            "type": "none", "host": "", "path": "", "tls": "tls" if p.get('tls') else ""
                        }
                        v_b64 = base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"vmess://{v_b64}")

                    # 3. Парсинг TROJAN из структуры YAML
                    elif p_type == 'trojan':
                        link = f"trojan://{uuid}@{server}:{port}#{name}"
                        extracted_proxies.append(link)

                    # 4. Парсинг SHADOWSOCKS (SS) из структуры YAML
                    elif p_type == 'ss':
                        cipher = p.get('cipher', 'aes-256-gcm')
                        user_info = base64.b64encode(f"{cipher}:{uuid}".encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"ss://{user_info}@{server}:{port}#{name}")

                    # 5. Парсинг ТУИЦ / ХИСТЕРИЯ (Если они есть в продвинутых Clash-мета сборках)
                    elif p_type in ['hysteria', 'hysteria2', 'hy2']:
                        extracted_proxies.append(f"hysteria2://{uuid}@{server}:{port}#{name}")
                    elif p_type == 'tuic':
                        extracted_proxies.append(f"tuic://{uuid}@{server}:{port}#{name}")

                except Exception:
                    continue
        except Exception:
            pass
        return extracted_proxies

    def collect_raw_sources(self):
        print(f"\n📡 [RAW-COLLECTOR] Запуск базового цеха с поддержкой Гитхаб RAW YAML...")
        collected_lines = []
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        for url in self.sources:
            print(f"📥 Извлекаю данные по RAW-ссылке: {url}")
            try:
                response = requests.get(url, headers=headers, timeout=12)
                if response.status_code != 200:
                    print(f"⚠️ Источник ответил ошибкой: {response.status_code}")
                    continue
                
                content = response.text
                
                # 🛠️ УМНАЯ ПРОВЕРКА НА YAML
