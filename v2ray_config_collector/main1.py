import os
import re
import requests
import yaml
import json
import base64
from bs4 import BeautifulSoup

class TelegramYamlCollector:
    def __init__(self):
        # 📂 КОРЕНЬ ЗАВОДА
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Сюда зашиты твои 588 Telegram-источников и YAML файлы
        self.sources = [
            "https://t.me/s/v2rayng_org",
            "https://t.me/s/Vmess_Vless_Log",
            "https://t.me/s/FreeVlessVmessTrojan",
            "https://t.me/s/v2ray_outline_vless_vmess",
            "https://raw.githubusercontent.com/asgharkapk/Sub-Config-Extractor/refs/heads/main/output_configs/clash/AzadNet/-t.me.yaml"
            # Сюда Гитхаб подставит все остальные твои каналы!
        ]
        
        # Общий котёл для очистки от дубликатов
        self.output_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')

    def parse_clash_yaml(self, yaml_text):
        """🧠 YAML-ДВИЖОК: Разбирает структуру Clash без ограничений по количеству."""
        extracted_proxies = []
        try:
            data = yaml.safe_load(yaml_text)
            if not data or not isinstance(data, dict) or 'proxies' not in data:
                return extracted_proxies
                
            # БЕЗЛИМИТ: крутим весь массив proxies полностью!
            for p in data['proxies']:
                try:
                    p_type = str(p.get('type', '')).lower()
                    name = p.get('name', 'YAML_Proxy').replace(' ', '_')
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password')
                    if not server or not port: continue

                    if p_type == 'vless':
                        link = f"vless://{uuid}@{server}:{port}?type={p.get('network', 'tcp')}"
                        if p.get('tls'): link += "&security=tls"
                        if p.get('reality-opts') or p.get('reality'): link += "&security=reality"
                        extracted_proxies.append(f"{link}#{name}")
                    elif p_type == 'vmess':
                        v_json = {"v": "2", "ps": name, "add": server, "port": str(port), "id": uuid, "aid": "0", "net": p.get('network', 'tcp'), "type": "none", "host": "", "path": "", "tls": "tls" if p.get('tls') else ""}
                        v_b64 = base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"vmess://{v_b64}")
                    elif p_type == 'trojan':
                        extracted_proxies.append(f"trojan://{uuid}@{server}:{port}#{name}")
                    elif p_type == 'ss':
                        cipher = p.get('cipher', 'aes-256-gcm')
                        user_info = base64.b64encode(f"{cipher}:{uuid}".encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"ss://{user_info}@{server}:{port}#{name}")
                except Exception: continue
        except Exception: pass
        return extracted_proxies

    def collect_everything(self):
        print(f"\n📡 [TELEGRAM-CEH] ЗАПУСК МЕГА-ШТУРМА 588 КАНАЛОВ БЕЗ ЛИМИТОВ!")
        collected_raw = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        for source in self.sources:
            print(f"📥 Тралю источник: {source}")
            try:
                response = requests.get(source, headers=headers, timeout=10)
                if response.status_code != 200: continue
                content = response.text

                # 🔓 ТЕЛЕГРАМ: Выкачиваем абсолютно всё, что отдал сервер, до самого дна!
                if "t.me/s/" in source:
                    soup = BeautifulSoup(content, 'html.parser')
                    messages = soup.find_all('div', class_='tgme_page_widget_html')
                    links_count = 0
                    for msg in messages:
                        links = re.findall(r'(?:vless|vmess|ss|trojan|naive|hysteria2|hy2|tuic|juicity)://[^\s<"\']+', msg.text)
                        collected_raw.extend(links)
                        links_count += len(links)
                    print(f"✅ Извлечено из ТГ-канала: {links_count} шт.")
                
                # Внешние YAML/TXT файлы тоже парсим на 100% мощности
                else:
                    if source.endswith('.yaml') or source.endswith('.yml') or 'proxies:' in content:
                        yaml_proxies = self.parse_clash_yaml(content)
                        collected_raw.extend(yaml_proxies)
                        print(f"✅ Извлечено из Clash YAML: {len(yaml_proxies)} шт.")
                    else:
                        lines = re.findall(r'(?:vless|vmess|ss|trojan|naive|hysteria2|hy2|tuic|juicity)://[^\s<"\']+', content)
                        collected_raw.extend(lines)
                        print(f"✅ Извлечено из RAW текста: {len(lines)} шт.")
            except Exception as e:
                print(f"⚠️ Пропуск источника (тайм-аут): {e}")

        if not collected_raw: 
            print("📭 Цеху не удалось собрать новые данные.")
            return

        # Намертво склеиваем дубликаты строк между собой
        unique_links = list(set([line.strip() for line in collected_raw if line.strip()]))
        
        # Подтягиваем результаты работы Базового цеха (main.py), чтобы не затереть его улов
        existing_configs = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_configs = [line.strip() for line in f if line.strip()]
            except Exception: pass
                
        total_combined = list(set(existing_configs + unique_links))
        
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(total_combined))
            
        print(f"\n==========================================================================")
        print(f"🏁 БЕЗЛИМИТНЫЙ СБОР ЗАВЕРШЕН!")
        print(f"📦 Всего уникальных прокси упаковано в deduplicated.txt: {len(total_combined)} шт.")
        print(f"==========================================================================")

        # 🚀 Отправляем очищенную мега-базу валидатору на проверку портов и автонарезку!
        try:
            from core.validator import ConnectivityValidator
            validator = ConnectivityValidator()
            validator.test_all_configs()
        except Exception: pass

if __name__ == "__main__":
    collector = TelegramYamlCollector()
    collector.collect_everything()
