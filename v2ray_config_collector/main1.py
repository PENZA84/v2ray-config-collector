import os
import re
import requests
import yaml
from bs4 import BeautifulSoup
from tqdm import tqdm

class TelegramYamlCollector:
    def __init__(self):
        # 📂 КОРЕНЬ ЗАВОДА
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Список Телеграм-каналов и внешних источников (сюда же можно вшивать YAML подписки)
        self.sources = [
            "https://t.me/s/v2rayng_org",
            "https://t.me/s/Vmess_Vless_Log",
            "https://t.me/s/FreeVlessVmessTrojan",
            "https://t.me/s/v2ray_outline_vless_vmess",
            # Прямая YAML подписка, которую ты дал, как пример для теста завода:
            "https://raw.githubusercontent.com/asgharkapk/Sub-Config-Extractor/refs/heads/main/output_configs/clash/AzadNet/-t.me.yaml"
        ]
        
        # Куда складываем сырую кучу перед дедупликацией и нарезкой
        self.output_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')

    def parse_clash_yaml(self, yaml_text):
        """
        🧠 YAML-ДВИЖОК: Потрошит структуру Clash/Mihomo подписок.
        Превращает структурированный YAML в стандартные прокси-ссылки v2rayN/Throne.
        """
        extracted_proxies = []
        try:
            # Безопасно загружаем YAML-структуру
            data = yaml.safe_load(yaml_text)
            if not data or not isinstance(data, dict) or 'proxies' not in data:
                return extracted_proxies

            for p in data['proxies']:
                try:
                    p_type = str(p.get('type', '')).lower()
                    name = p.get('name', 'YAML_Proxy')
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password') # Для VMess/VLESS/Trojan
                    
                    if not server or not port:
                        continue

                    # 1. Сборка VLESS из YAML
                    if p_type == 'vless':
                        link = f"vless://{uuid}@{server}:{port}?type={p.get('network', 'tcp')}"
                        if p.get('tls'): link += "&security=tls"
                        if p.get('reality-opts'): link += "&security=reality"
                        link += f"#{name}"
                        extracted_proxies.append(link)

                    # 2. Сборка VMESS из YAML
                    elif p_type == 'vmess':
                        v_json = {
                            "v": "2", "ps": name, "add": server, "port": str(port),
                            "id": uuid, "aid": "0", "net": p.get('network', 'tcp'),
                            "type": "none", "host": "", "path": "", "tls": "tls" if p.get('tls') else ""
                        }
                        v_b64 = base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"vmess://{v_b64}")

                    # 3. Сборка TROJAN из YAML
                    elif p_type == 'trojan':
                        link = f"trojan://{uuid}@{server}:{port}#{name}"
                        extracted_proxies.append(link)

                    # 4. Сборка SHADOWSOCKS (SS) из YAML
                    elif p_type == 'ss':
                        cipher = p.get('cipher', 'aes-256-gcm')
                        # Формируем стандартную строку ss://
                        user_info = base64.b64encode(f"{cipher}:{uuid}".encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"ss://{user_info}@{server}:{port}#{name}")

                except Exception:
                    continue
        except Exception:
            pass
        return extracted_proxies

    def collect_everything(self):
        print(f"\n📡 [TELEGRAM-CEH] Запуск парсера Телеграма и YAML-источников...")
        collected_raw = []

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        for source in self.sources:
            print(f"📥 Сканирую источник: {source}")
            try:
                response = requests.get(source, headers=headers, timeout=10)
                if response.status_code != 200:
                    continue
                
                content = response.text

                # Проверяем, если ссылка ведёт на YAML файл
                if source.endswith('.yaml') or source.endswith('.yml') or 'proxies:' in content:
                    yaml_proxies = self.parse_clash_yaml(content)
                    collected_raw.extend(yaml_proxies)
                    print(f"🧠 Извлечено из YAML-структуры: {len(yaml_proxies)} прокси.")
                else:
                    # Обычный парсинг Телеграм-канала через BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    messages = soup.find_all('div', class_='tgme_page_widget_html')
                    
                    for msg in messages:
                        # Ищем регулярками стандартные ссылки vless, vmess, ss, trojan, naive
                        links = re.findall(r'(?:vless|vmess|ss|trojan|naive(?:\+https)?|hysteria2|hy2|tuic|juicity)://[^\s<"\']+', msg.text)
                        collected_raw.extend(links)
            except Exception as e:
                print(f"⚠️ Ошибка при обработке {source}: {e}")

        if not collected_raw:
            print("📭 Не удалось собрать новые ссылки.")
            return

        # Убираем грубые дубликаты строк перед валидацией
        unique_links = list(set([line.strip() for line in collected_raw if line.strip()]))
        
        # Складываем в папку unique для нашего валидатора-нарезчика
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(unique_links))

        print(f"\n==========================================================================")
        print(f"🏁 ПЕРВИЧНЫЙ СБОР ЗАВЕРШЕН!")
        print(f"📥 Всего собрано и упаковано в deduplicated.txt: {len(unique_links)} шт.")
        print(f"==========================================================================")

        # 🚀 Автоматический пинок валидатору, чтобы он сразу отсортировал и нарезал базу!
        try:
            from core.validator import ConnectivityValidator
            validator = ConnectivityValidator()
            validator.test_all_configs()
        except ImportError:
            print("⚠️ Не удалось запустить валидатор напрямую, он отработает на следующем шаге Гита.")

if __name__ == "__main__":
    collector = TelegramYamlCollector:
    collector.collect_everything()
