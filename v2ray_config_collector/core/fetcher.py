import os
import requests

class SourceCollector:
    def __init__(self, input_file='data/sources/sources.txt', stats_dict=None):
        self.input_file = input_file
        self.stats = stats_dict if stats_dict is not None else {}

    def read_links(self):
        try:
            if not os.path.exists(self.input_file):
                return []
            with open(self.input_file, 'r', encoding='utf-8') as f:
                raw_links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            seen = set()
            unique_links = []
            duplicates = []
            for link in raw_links:
                if link in seen:
                    duplicates.append(link)
                else:
                    seen.add(link)
                    unique_links.append(link)

            if duplicates:
                dup_path = os.path.join(os.path.dirname(self.input_file), 'duplicate_URL_sources.txt')
                with open(dup_path, 'w', encoding='utf-8') as f:
                    for d in duplicates:
                        f.write(d + '\n')
            
            if hasattr(self, 'stats') and isinstance(self.stats, dict):
                self.stats['total_links'] = len(unique_links)
            return unique_links
        except Exception as e:
            print(f"Ошибка в read_links: {e}")
            return []

    def fetch_all_configs(self):
        links = self.read_links()
        print(f"Уникальных ссылок для обработки: {len(links)}")
        
        all_content = []
        for link in links:
            try:
                # Скачиваем содержимое каждой ссылки
                response = requests.get(link, timeout=10)
                if response.status_code == 200:
                    all_content.append(response.text)
            except Exception as e:
                print(f"Не удалось скачать {link}: {e}")

        if not all_content:
            print("Ничего не удалось скачать!")
            return

        # СОЗДАЕМ ТЕ САМЫЕ ФАЙЛЫ, КОТОРЫЕ ИЩЕТ ПАРСЕР
        os.makedirs('data/raw', exist_ok=True)
        
        with open('data/raw/raw_configs.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
            
        print(f"Успешно скачано данных из {len(all_content)} источников.")
