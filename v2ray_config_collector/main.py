import os
import sys

# Добавляем путь к core, чтобы Python видел наши модули
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def main():
    # Определение базового пути (корень v2ray_config_collector)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. ПУТИ ДАННЫХ (строго по стандарту проекта)
    raw_path = os.path.join(base_dir, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(base_dir, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(base_dir, 'data', 'validated', 'all_valid.txt')

    print("🚀 Запуск полного цикла сборки и проверки...")

    # ШАГ 1: Сбор сырых данных (Fetcher)
    # Берет ссылки из data/sources/sources.txt -> качает в data/raw/raw_configs.txt
    print("\n--- Шаг 1: Сбор данных ---")
    fetcher = ConfigFetcher()
    fetcher.fetch_all()

    # ШАГ 2: Парсинг и конвертация (Parser)
    # Читает raw_configs.txt -> создает deduplicated.txt и dns_list.txt в data/unique/
    print("\n--- Шаг 2: Парсинг и поиск DNS ---")
    parser = FormatConverter(input_files=[raw_path], output_dir=unique_dir)
    parser.process()

    # ШАГ 3: Удаление дубликатов (Deduplicator)
    # Чистит deduplicated.txt от повторов
    print("\n--- Шаг 3: Дедупликация ---")
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    # ШАГ 4: Валидация (Validator)
    # Проверяет deduplicated.txt -> сохраняет живые в data/validated/all_valid.txt
    print("\n--- Шаг 4: Валидация (TCP-проверка) ---")
    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    print("\n✅ Цикл завершен успешно!")

if __name__ == "__main__":
    main()
