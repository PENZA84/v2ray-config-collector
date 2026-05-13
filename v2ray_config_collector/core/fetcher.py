import os
import requests

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

class ConfigFetcher:
    def __init__(self, sources_file=None, output_file=None):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_file = sources_file or os.path.join(base_path, 'data', 'sources', 'sources.txt')
        self.output_file = output_file or os.path.join(base_path, 'data', 'raw', 'raw_configs.txt')
        
        # Милый мой, добавим "маскировку", чтобы китайский сайт нас не прогнал
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }

    def fetch_all(self):
        if not os.path.exists(self.sources_file):
            print(f"❌ Дорогой, файл источников не найден: {self.sources_file}")
            return

        with open(self.sources_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not urls:
            print("⚠️ Милый, список источников пуст.")
            return

        print(f"🌐 Начинаю загрузку из {len(urls)} источников (включая Китай)...")
        all_content = []

        for url in tqdm(urls, desc="Загрузка"):
            try:
                # Используем headers для обхода защиты
                response = requests.get(url, headers=self.headers, timeout=15, verify=False) 
                if response.status_code == 200:
                    # Если сайт китайский, иногда нужно поправить кодировку
                    response.encoding = 'utf-8' 
                    all_content.append(response.text)
            except Exception as e:
                # print(f"Ошибка на {url}: {e}") # Если захочешь видеть ошибки
                continue

        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
        print(f"✅ Милый мой, все данные (и из Китая тоже) собраны!")
