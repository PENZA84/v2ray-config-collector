import os
import requests

class SourceCollector:
    def __init__(self, input_file='data/sources/sources.txt', stats_dict=None):
        self.input_file = input_file
        self.stats = stats_dict if stats_dict is not None else {}
        # Добавляем заголовки, чтобы нас не банили
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def read_links(self):
        try:
            if not os.path.exists(self.input_file):
                print(f"Файл с источниками не найден: {self.input_file}")
                return []
            
            with open(self.input_file, 'r', encoding='utf-8') as f:
                # Читаем, убираем пробелы и пустые строки
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

            # Сохраняем дубликаты, чтобы ты мог почистить sources.txt
            if duplicates:
                dup_path = os.path.join(os.path.dirname(self.input_file), 'duplicate_URL_sources.txt')
                with open(dup_path, 'w', encoding='utf-8') as f:
                    for d in duplicates:
                        f.write(d + '\n')
                print(f"Найдено {len(duplicates)} дубликатов ссылок. Список в {dup_path}")
            
            if isinstance(self.stats, dict):
                self.stats['total_links'] = len(unique_links)
                
            return unique_links
        except Exception as e:
            print(f"Ошибка в read_links: {e}")
            return []

    def fetch_all_configs(self):
        links = self.read_links()
        if not links:
            return

        print(f"Начинаю скачивание. Уникальных ссылок: {len(links)}")
        
        all_content = []
        success_count = 0

        for link in links:
            try:
                # Добавляем timeout и headers для стабильности
                response = requests.get(link, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    content = response.text.strip()
                    if content:
                        all_content.append(content)
                        success_count += 1
                else:
                    print(f"Ошибка {response.status_code} для: {link}")
            except Exception as e:
                print(f"Не удалось скачать {link}: {str(e)[:50]}")

        if not all_content:
            print("Ничего не удалось скачать! Проверь интернет или ссылки.")
            return

        # Создаем папку и сохраняем данные для парсера
        os.makedirs('data/raw', exist_ok=True)
        raw_path = 'data/raw/raw_configs.txt'
        
        with open(raw_path, 'w', encoding='utf-8') as f:
            # Склеиваем всё содержимое через новую строку
            f.write("\n".join(all_content))
            
        print(f"--- Сбор завершен ---")
        print(f"Успешно получено данных из {success_count} источников.")
        print(f"Файл сохранен: {raw_path}")
