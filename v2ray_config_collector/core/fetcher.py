import requests
import os

class SourceCollector:
    def __init__(self, source_file=None, output_file=None):
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Твой файл со списком 5030 источников
        self.source_file = source_file or os.path.join(package_dir, 'data', 'sources', 'sources.txt')
        # Куда сохраняем "улов"
        self.output_file = output_file or os.path.join(package_dir, 'data', 'raw', 'raw_configs.txt')

    def fetch_all_configs(self):
        if not os.path.exists(self.source_file):
            print(f"❌ Файл источников не найден: {self.source_file}")
            return

        with open(self.source_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"🚀 Начинаю сбор. В списке: {len(urls)} ссылок.")
        
        all_content = []
        clean_urls = [] 

        for url in urls:
            # Сохраняем комментарии
            if url.startswith('#'):
                clean_urls.append(url)
                continue

            try:
                # Уменьшил таймаут до 5 секунд для ускорения процесса
                response = requests.get(url, timeout=5, allow_redirects=True)
                
                if response.status_code == 200:
                    all_content.append(response.text)
                    clean_urls.append(url)
                elif response.status_code == 404:
                    print(f"🗑 Удаляю (404): {url}")
                else:
                    # Для всех остальных ошибок (500, 429) пока оставляем
                    print(f"⚠️ Статус {response.status_code}, оставляю: {url}")
                    clean_urls.append(url)
            
            except Exception:
                # При ошибке сети оставляем ссылку, чтобы не удалить лишнее
                print(f"📡 Тайм-аут или ошибка сети: {url}")
                clean_urls.append(url)

        # Перезапись sources.txt (Генеральная уборка)
        with open(self.source_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(clean_urls))

        # ГАРАНТИЯ: Создаем папку data/raw если её нет
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
            
        print(f"✨ Готово! Список очищен. Осталось источников: {len(clean_urls)}")
