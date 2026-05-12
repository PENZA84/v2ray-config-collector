import os
import sys

# Добавляем путь к core
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir) # Корень всего репозитория

    # ПУТИ ДАННЫХ
    raw_path = os.path.join(base_dir, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(base_dir, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(base_dir, 'data', 'validated', 'all_valid.txt')
    
    # 1. АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ПАПОК (Исправляет ошибку 830)
    for folder in [os.path.join(base_dir, 'data', 'sources'), 
                   os.path.join(base_dir, 'data', 'raw'), 
                   unique_dir, 
                   os.path.join(base_dir, 'data', 'validated')]:
        os.makedirs(folder, exist_ok=True)

    # 2. УМНЫЙ ПОИСК CLEANED_URLS (Исправляет ситуацию 831)
    # Ищем сначала в папке sources, если нет - в корне репозитория
    cleaned_file = os.path.join(base_dir, 'data', 'sources', 'cleaned_urls.txt')
    if not os.path.exists(cleaned_file):
        cleaned_file = os.path.join(root_dir, 'cleaned_urls.txt')

    print(f"🚀 Запуск завода. Проверка путей...")

    # ШАГ 1: Сбор данных
    print("\n--- Шаг 1: Сбор данных ---")
    fetcher = ConfigFetcher()
    fetcher.fetch_all() 

    # ШАГ 2: Парсинг
    input_files = [raw_path]
    if os.path.exists(cleaned_file):
        print(f"🔗 Подключаю найденный файл: {cleaned_file}")
        input_files.append(cleaned_file)
    else:
        print(f"⚠️ Файл cleaned_urls.txt не найден ни в папке, ни в корне.")

    print("\n--- Шаг 2: Извлечение конфигов ---")
    parser = FormatConverter(input_files=input_files, output_dir=unique_dir)
    parser.process()

    # ШАГ 3: Дедупликация
    print("\n--- Шаг 3: Удаление дубликатов ---")
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    # ШАГ 4: Валидация
    print("\n--- Шаг 4: Финальный фильтр ---")
    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    print("\n✅ Цикл завершен успешно!")

if __name__ == "__main__":
    main()
