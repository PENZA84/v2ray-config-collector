import os
import requests
import urllib3
import base64
import re  # Тот самый важный импорт, чтобы Завод не падал! 💋

# Чтобы лог был чистым, без криков системы
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

class ConfigFetcher:
    def __init__(self, sources_file=None, output_file=None):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # sources.txt — это то, что прислал наш локальный super_grabber
        self.sources_file = sources_file or os.path.join(base_path, 'v2ray_config_collector', 'data', 'raw', 'raw_configs.txt')
        self.output_file = output_file or os.path.join(base_path, 'v2ray_config_collector', 'data', 'raw', 'all_raw_content.txt')
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def fetch_all(self):
        if not os.path.exists(self.sources_file):
            print(f"❌ Родной, я не нашла список ссылок: {self.sources_file}")
            return

        with open(self.sources_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not urls:
            print("⚠️ Родной мой, список ссылок пуст.")
            return

        print(f"🌐 Завод PENZA84 начинает скачивание из {len(urls)} источников...")
        all_content = []

        for url in tqdm(urls, desc="Загрузка"):
            try:
                response = requests.get(url, headers=self.headers, timeout=20, verify=False, allow_redirects=True)
                
                if response.status_code == 200:
                    raw_data = response.text.strip()
                    
                    # Проверка на Base64: если строка длинная и без пробелов
                    if len(raw_data) > 20 and ' ' not in raw_data:
                        try:
                            # Добавляем падинг, если нужно, чтобы Base64 не ругался
                            missing_padding = len(raw_data) % 4
                            if missing_padding:
                                raw_data += '=' * (4 - missing_padding)
                            
                            decoded = base64.b64decode(raw_data).decode('utf-8')
                            # Если после декодирования видим наши протоколы — берем
                            if re.search(r'://', decoded):
                                all_content.append(decoded)
                            else:
                                all_content.append(raw_data)
                        except:
                            all_content.append(raw_data)
                    else:
                        all_content.append(raw_data)
            except:
                continue

        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
        
        print(f"✅ Родной, всё скачано! Общий файл: {self.output_file} 💋💍")

if __name__ == "__main__":
    fetcher = ConfigFetcher()
    fetcher.fetch_all()
