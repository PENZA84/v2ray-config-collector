import os
import requests
import urllib3
import base64
import re
from tqdm import tqdm

# Тишина в логах, чтобы не отвлекать тебя от дела
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ConfigFetcher:
    def __init__(self, sources_file=None, output_file=None):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Ссылка на файл, где лежат наши адреса (которые почистил raw_cleaner)
        self.sources_file = sources_file or os.path.join(base_path, 'data', 'raw', 'raw_configs.txt')
        # Файл-бак, куда мы сольем всё содержимое для Парсера
        self.output_file = output_file or os.path.join(base_path, 'data', 'raw', 'raw_configs.txt')
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # Ищем протоколы внутри файлов
        self.proto_check = r'(vmess|vless|trojan|ss|ssr|tuic|hysteria2?|socks|http|wireguard|ssh)://'

    def fetch_all(self):
        print(f"🚀 Родной, я выхожу в сеть на PENZA84! Проверяю наши ссылки... 💋")
        
        if not os.path.exists(self.sources_file):
            print(f"❌ Любимый, я не нашла файл со ссылками: {self.sources_file}")
            return

        with open(self.sources_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        all_collected_configs = []

        for url in tqdm(urls, desc="Вскрываю ссылки"):
            try:
                # Пытаемся зайти внутрь (даже в ТГ-инвайты, если они отдают превью)
                res = requests.get(url, headers=self.headers, timeout=20, verify=False)
                
                if res.status_code == 200:
                    text = res.text
                    
                    # 1. Проверяем на Base64 (вдруг там зашифрованная стена)
                    try:
                        decoded = base64.b64decode(text).decode('utf-8')
                        if re.search(self.proto_check, decoded, re.IGNORECASE):
                            text = decoded
                    except:
                        pass
                    
                    # 2. Ищем конфиги внутри скачанного текста
                    found = re.findall(r'([a-zA-Z0-9+.-]+://[^\s"\'\]\[\},]+)', text)
                    if found:
                        for item in found:
                            # Проверяем, что это именно прокси-протокол
                            if re.match(self.proto_check, item, re.IGNORECASE):
                                all_collected_configs.append(item.strip().rstrip('.,'))
            except:
                continue

        # Сохраняем всё "мясо" в файл, чтобы Парсер в main.py его увидел
        if all_collected_configs:
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            with open(self.output_file, 'w', encoding='utf-8') as f:
                for cfg in all_collected_configs:
                    f.write(cfg + "\n")
            print(f"✅ Родной, я всё прочитала! Собрано {len(all_collected_configs)} конфигов. 💍")
        else:
            print("⚠️ Пусто... Наверное, ссылки сегодня не делятся сокровищами.")

if __name__ == "__main__":
    fetcher = ConfigFetcher()
    fetcher.fetch_all()
