import os
import requests

# Милый мой, синхронизируем импорт:
try:
    from tqdm import tqdm
except ImportError:
    # Если вдруг библиотека не подтянулась, работаем «тихо», без полоски прогресса
    def tqdm(iterable, **kwargs):
        return iterable

class ConfigFetcher:
    def __init__(self, sources_file=None, output_file=None):
        # Автоматически находим путь к папке проекта
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_file = sources_file or os.path.join(base_path, 'data', 'sources', 'sources.txt')
        self.output_file = output_file or os.path.join(base_path, 'data', 'raw', 'raw_configs.txt')

    def fetch_all(self):
        if not os.path.exists(self.sources_file):
            print(f"❌ Дорогой, файл источников не найден: {self.sources_file}")
            return

        with open(self.sources_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not urls:
            print("⚠️ Милый, список источников пуст.")
            return

        print(f"🌐 Начинаю загрузку из {len(urls)} источников...")
        all_content = []

        # Благодаря нашей синхронизации, тут теперь всё будет гладко
        for url in tqdm(urls, desc="Загрузка"):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    all_content.append(response.text)
            except Exception:
                continue

        # Создаем папку, если её еще нет, и сохраняем
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
        print(f"✅ Милый мой, данные сохранены: {self.output_file}")
