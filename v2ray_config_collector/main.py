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
        
        # Список RAW-ссылок (сюда зашиты текстовые подписки, гитхаб-источники и пулы)
        self.sources = [
            "https://raw.githubusercontent.com/asgharkapk/Sub-Config-Extractor/refs/heads/main/output_configs/clash/AzadNet/-t.me.yaml",
            "https://raw.githubusercontent.com/w1770946466/Auto_Proxy/main/Long_term_subscription_num",
            "https://raw.githubusercontent.com/zu1k/proxypool/master/config/source.yaml"
        ]
        
        # Наш царский список ключевых слов для умного фильтра по первой строчке
        self.target_protocols = ["trojan", "vless", "vmess", "ss", "shadowsocks", "hysteria", "hy2", "naive", "tuic", "juicity"]
        
        # Временный накопитель для сырых строк перед фильтрацией и нарезкой
        self.output_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')

    def parse_clash_yaml(self, yaml_text):
        """🧠 YAML-ДВИЖОК: Разбирает структуру Clash/Mihomo подписок."""
        extracted_proxies = []
        try:
            data = yaml.safe_load(yaml_text)
            if not data or not isinstance(data, dict) or 'proxies' not in data:
                return extracted_proxies

            for p in data['proxies']:
                try:
                    p_type = str(p.get('type', '')).lower()
                    name = p.get('name', 'RAW_YAML_Proxy').replace(' ', '_')
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password')
                    
                    if not server or not port:
                        continue

                    if p_type == 'vless':
                        link = f"vless://{uuid}@{server}:{port}?type={p.get('network', 'tcp')}"
                        if p.get('tls'): link += "&security=tls"
                        if p.get('reality-opts') or p.get('reality'): link += "&security=reality"
                        link += f"#{name}"
                        extracted_proxies.append(link)

                    elif p_type == 'vmess':
                        v_json = {
                            "v": "2", "ps": name, "add": server, "port": str(port),
                            "id": uuid, "aid": "0", "net": p.get('network', 'tcp'),
                            "type": "none", "host": "", "path": "", "tls": "tls" if p.get('tls') else ""
                        }
                        v_b64 = base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"vmess://{v_b64}")

                    elif p_type == 'trojan':
                        extracted_proxies.append(f"trojan://{uuid}@{server}:{port}#{name}")

                    elif p_type == 'ss':
                        cipher = p.get('cipher', 'aes-256-gcm')
                        user_info = base64.b64encode(f"{cipher}:{uuid}".encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"ss://{user_info}@{server}:{port}#{name}")

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
        print(f"\n📡 [RAW-COLLECTOR] Запуск базового цеха с умным фильтром протоколов...")
        collected_lines = []
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        for url in self.sources:
            print(f"\n🔍 Проверяю источник: {url}")
            try:
                response = requests.get(url, headers=headers, timeout=12)
                if response.status_code != 200:
                    print(f"⚠️ Ошибка доступа: {response.status_code}")
                    continue
                
                content = response.text
                lines_of_content = content.splitlines()
                
                if not lines_of_content:
                    continue
                
                # 🎯 ТВОЯ ИДЕЯ: Берем первую строчку файла для быстрого анализа!
                first_line = lines_of_content[0].lower()
                print(f"📋 Первая строчка источника: '{lines_of_content[0][:60]}...'")
                
                # Проверяем, есть ли в первой строчке или названии наши рабочие протоколы
                has_target_protocol = any(proto in first_line or proto in url.lower() for proto in self.target_protocols)
                
                # Если файл зашифрован в Base64, первая строчка может не содержать слов, делаем доп. проверку содержимого
                if not has_target_protocol and ('proxies:' in content or '://' in content):
                    has_target_protocol = True
                
                if not has_target_protocol:
                    print("⏭️ Пропускаем! Нужных протоколов (Trojan/VLESS/VMess) в заголовке не обнаружено.")
                    continue
                
                print("🎯 Фильтр пройден! Обнаружены целевые протоколы. Начинаю полный сбор...")
                
                # 🛠️ РАЗБОР ПОТИПОВО
                if url.endswith('.yaml') or url.endswith('.yml') or 'proxies:' in content:
                    yaml_proxies = self.parse_clash_yaml(content)
                    collected_lines.extend(yaml_proxies)
                    print(f"✅ Извлечено из YAML: {len(yaml_proxies)} прокси-ссылок.")
                else:
                    # Текстовый файл подписки
                    links = re.findall(r'(?:vless|vmess|ss|trojan|naive(?:\+https)?|hysteria2|hy2|tuic|juicity)://[^\s<"\']+', content)
                    collected_lines.extend(links)
                    print(f"✅ Извлечено из текста: {len(links)} прокси-ссылок.")
                    
            except Exception as e:
                print(f"⚠️ Ошибка при обработке источника {url}: {e}")

        if not collected_lines:
            print("\n📭 После фильтрации ничего нового не собрано.")
            return

        # Первичная зачистка дубликатов строк
        clean_raw_list = list(set([line.strip() for line in collected_lines if line.strip()]))
        
        # Сохранение в общий котел unique
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        existing_configs = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_configs = [line.strip() for line in f if line.strip()]
            except Exception:
                pass
        
        total_combined = list(set(existing_configs + clean_raw_list))

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(total_combined))

        print(f"\n==========================================================================")
        print(f"🏁 БАЗОВЫЙ ЦЕХ ОТРАБОТАЛ ПО НОВОМУ АЛГОРИТМУ!")
        print(f"📦 Всего уникальных строк отправлено валидатору: {len(total_combined)} шт.")
        print(f"==========================================================================")

if __name__ == "__main__":
    collector = RawConfigsCollector()
    collector.collect_raw_sources()
