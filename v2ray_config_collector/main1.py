import os
import re
import requests
import yaml
import json
import base64
from bs4 import BeautifulSoup
from tqdm import tqdm

class TelegramYamlCollector:
    def __init__(self):
        # 📂 КОРЕНЬ ЗАВОДА
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Список Телеграм-каналов и внешних YAML источников
        self.sources = [
            "https://t.me/s/v2rayng_org",
            "https://t.me/s/Vmess_Vless_Log",
            "https://t.me/s/FreeVlessVmessTrojan",
            "https://t.me/s/v2ray_outline_vless_vmess",
            "https://raw.githubusercontent.com/asgharkapk/Sub-Config-Extractor/refs/heads/main/output_configs/clash/AzadNet/-t.me.yaml"
        ]
        
        # Наш царский список ключевых слов для экспресс-фильтрации
        self.target_protocols = ["trojan", "vless", "vmess", "ss", "shadowsocks", "hysteria", "hy2", "naive", "tuic", "juicity"]
        
        # Куда складываем сырую кучу перед дедупликацией и нарезкой
        self.output_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')

    def parse_clash_yaml(self, yaml_text):
        """🧠 YAML-ДВИЖОК: Потрошит структуру Clash/Mihomo подписок."""
        extracted_proxies = []
        try:
            data = yaml.safe_load(yaml_text)
            if not data or not isinstance(data, dict) or 'proxies' not in data:
                return extracted_proxies

            for p in data['proxies']:
                try:
                    p_type = str(p.get('type', '')).lower()
                    name = p.get('name', 'YAML_Proxy').replace(' ', '_')
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

                except Exception:
                    continue
        except Exception:
            pass
        return extracted_proxies

    def collect_everything(self):
        print(f"\n📡 [TELEGRAM-CEH] Запуск парсера Телеграма с экспресс-фильтром протоколов...")
        collected_raw = []

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        for source in self.sources:
            print(f"\n🔍 Сканирую источник: {source}")
            try:
                response = requests.get(source, headers=headers, timeout=12)
                if response.status_code != 200:
                    continue
                
                content = response.text
                lines_of_content = content.splitlines()
                
                if not lines_of_content:
                    continue
                
                # 🎯 ТВОЙ АЛГОРИТМ: Экспресс-анализ первой строчки или названия источника!
                first_line = lines_of_content[0].lower()
                
                # Проверяем, есть ли в первой строчке, коде или URL наши протоколы
                has_target_protocol = any(proto in first_line or proto in source.lower() for proto in self.target_protocols)
                
                # Для каналов ТГ делаем доп. поблажку (так как там верстка HTML в начале файла)
                if "t.me/s/" in source:
                    has_target_protocol = True
                
                if not has_target_protocol:
                    print("箱 Пропускаем источник! Целевых протоколов (Trojan/VLESS) в заголовке нет.")
                    continue

                print("🎯 Фильтр пройден! Начинаю глубокий сбор данных...")

                # Проверяем, если ссылка ведёт на YAML файл
                if source.endswith('.yaml') or source.endswith('.yml') or 'proxies:' in content:
                    yaml_proxies = self.parse_clash_yaml(content)
                    collected_raw.extend(yaml_proxies)
                    print(f"✅ Извлечено из YAML-структуры: {len(yaml_proxies)} прокси.")
                else:
                    # Обычный парсинг Телеграм-канала через BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    messages = soup.find_all('div', class_='tgme_page_widget_html')
                    
                    channel_links_count = 0
                    for msg in messages:
                        links = re.findall(r'(?:vless|vmess|ss|trojan|naive(?:\+https)?|hysteria2|hy2|tuic|juicity)://[^\s<"\']+', msg.text)
                        collected_raw.extend(links)
                        channel_links_count += len(links)
                    print(f"✅ Извлечено из постов ТГ: {channel_links_count} прокси.")

            except Exception as e:
                print(f"⚠️ Ошибка при обработке {source}: {e}")

        if not collected_raw:
            print("\n📭 После экспресс-фильтрации ничего нового не найдено.")
            return

        # Убираем дубликаты строк перед валидацией
        unique_links = list(set([line.strip() for line in collected_raw if line.strip()]))
        
        # Подгружаем то, что уже успел собрать Базовый цех (main.py), чтобы не затереть его труды!
        existing_configs = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_configs = [line.strip() for line in f if line.strip()]
            except Exception:
                pass
                
        total_combined = list(set(existing_configs + unique_links))
        
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(total_combined))

        print(f"\n==========================================================================")
        print(f"🏁 ТЕЛЕГРАМ-ЦЕХ РАБОТУ ЗАВЕРШИЛ!")
        print(f"📥 Всего в общем котле deduplicated.txt лежит: {len(total_combined)} строк.")
        print(f"==========================================================================")

        # 🚀 Мгновенный пинок валидатору на нарезку!
        try:
            from core.validator import ConnectivityValidator
            validator = ConnectivityValidator()
            validator.test_all_configs()
        except Exception as e:
            print(f"⚠️ Валидатор будет запущен на следующем этапе сборки.")

if __name__ == "__main__":
    collector = TelegramYamlCollector()
    collector.collect_everything()
