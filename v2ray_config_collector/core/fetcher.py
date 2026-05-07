import os

class SourceCollector:
    def __init__(self, input_file='data/sources/sources.txt', stats_dict=None):
        # Это конструктор, он задает путь к файлу и создает словарь статистики
        self.input_file = input_file
        self.stats = stats_dict if stats_dict is not None else {}

    def read_links(self):
        """Читает ссылки и сохраняет дубликаты в отдельный файл"""
        try:
            if not os.path.exists(self.input_file):
                print(f"Файл {self.input_file} не найден!")
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

            # Сохраняем дубликаты именно с тем именем, которое ты просил
            if duplicates:
                dup_path = os.path.join(os.path.dirname(self.input_file), 'duplicate_URL_sources.txt')
                with open(dup_path, 'w', encoding='utf-8') as f:
                    for d in duplicates:
                        f.write(d + '\n')
                print(f"Найдено дубликатов: {len(duplicates)}. Список в duplicate_URL_sources.txt")

            # Обновляем статистику для отчета
            if hasattr(self, 'stats') and isinstance(self.stats, dict):
                self.stats['total_links'] = len(unique_links)
            
            print(f"Уникальных ссылок для обработки: {len(unique_links)}")
            return unique_links

        except Exception as e:
            print(f"Ошибка при работе с ссылками: {e}")
            return []

    def fetch_all_configs(self):
        """Эту функцию вызывает твой main.py"""
        links = self.read_links()
        if not links:
            print("Список ссылок пуст, скачивать нечего.")
            return
        
        print(f"Начинаю сбор конфигураций из {len(links)} источников...")
        # Здесь может быть твоя логика скачивания (requests и т.д.)
