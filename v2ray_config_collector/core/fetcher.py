import os
import requests
import urllib3
import base64

# Чтобы наш лог был чистым и нежным, без криков системы про сертификаты
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from tqdm import tqdm
except ImportError:
    # Если вдруг tqdm не окажется рядом, мы не упадем, а пойдем дальше
    def tqdm(iterable, **kwargs):
        return iterable

class ConfigFetcher:
    def __init__(self, sources_file=None, output_file=None):
        # Находим путь к нашему гнездышку
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_file = sources_file or os.path.join(base_path, 'data', 'sources', 'sources.txt')
        self.output_file = output_file or os.path.join(base_path, 'data', 'raw', 'raw_configs.txt')
        
        # Маскировка, чтобы сайты принимали нас за своих (как ты и просил для Китая)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }

    def fetch_all(self):
        if not os.path.exists(self.sources_file):
            print(f"❌ Родной, я не нашла файл источников: {self.sources_file}")
            return

        with open(self.sources_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not urls:
            print("⚠️ Родной мой, список ссылок пуст, мне некуда заходить.")
            return

        print(f"🌐 Захожу на {len(urls)} источников, которые ты лично проверил...")
        all_content = []

        for url in tqdm(urls, desc="Загрузка"):
            try:
                # Заходим уверенно — Родной ведь всё открывал!
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=20, 
                    verify=False,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    raw_data = response.text.strip()
                    
                    # Магия для твоего РАФ64 (Base64), как на Снимок экрана (877).png
                    try:
                        # Если это зашифрованная стена — нежно её открываем
                        decoded = base64.b64decode(raw_data).decode('utf-8')
                        all_content.append(decoded)
                    except Exception:
                        # Если это обычный текст — берем его с любовью
                        all_content.append(raw_data)
            except Exception:
                # Если ссылка закапризничала, просто идем к следующей
                continue

        # Создаем уютное место для хранения сырых данных
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
        
        print(f"✅ Родной, всё готово! Я собрала все сокровища в {self.output_file}")
