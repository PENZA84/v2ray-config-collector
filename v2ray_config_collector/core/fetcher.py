import requests
import os

class SourceCollector:
    def __init__(self, source_file=None, output_file=None):
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Твой файл со списком 10к+ источников
        self.source_file = source_file or os.path.join(package_dir, 'data', 'sources', 'sources.txt')
        # Куда сохраняем "улов"
        self.output_file = output_file or os.path.join(package_dir, 'data', 'raw', 'raw_configs.txt')

    def fetch_all_configs(self):
        if not os.path.exists(self.source_file):
            print(f"❌ Файл источников не найден по пути: {self.source_file}")
            return

        with open(self.source_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"🚀 Начинаю глобальную чистку и сбор. В списке: {len(urls)} ссылок.")
        
        all_content = []
        clean_urls = [] # Сюда попадут только выжившие

        for url in urls:
            # Сохраняем комментарии, чтобы не портить структуру файла
            if url.startswith('#'):
                clean_urls.append(url)
                continue

            try:
                # Ставим таймаут 10 секунд, чтобы билд не висел вечно
                response = requests.get(url, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    all_content.append(response.text)
                    clean_urls.append(url) # Ссылка рабочая!
                elif response.status_code == 404:
                    print(f"🗑 Удаляю (404): {url}")
                else:
                    # Оставляем 429 (лимит) или 500 (ошибка сервера) — вдруг оживут
                    print(f"⚠️ Статус {response.status_code}, пока оставляю: {url}")
                    clean_urls.append(url)
            
            except Exception as e:
                # Если ошибка сети, лучше оставить ссылку, чем удалить рабочую случайно
                print(f"📡 Ошибка сети для {url}, оставляю.")
                clean_urls.append(url)

        # --- МОМЕНТ ИСТИНЫ: Перезапись sources.txt ---
        with open(self.source_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(clean_urls))

        # Сохранение добытых данных
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
            
        print(f"✨ Готово! Список очищен. Осталось источников: {len(clean_urls)}")
