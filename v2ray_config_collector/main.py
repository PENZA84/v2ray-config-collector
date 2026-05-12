import os
import sys

# Добавляем путь к core, чтобы Python видел наши модули
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def main():
    # Базовый путь проекта
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ПУТИ ДАННЫХ
    raw_path = os.path.join(base_dir, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(base_dir, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(base_dir, 'data', 'validated', 'all_valid.txt')
    
    # Твои файлы управления ссылками
    sources_file = os.path.join(base_dir, 'data', 'sources', 'sources.txt')
    cleaned_file = os.path.join(base_dir, 'data', 'sources', 'cleaned_urls.txt')

    print(f"🚀 Завод в работе. Текущая задача: Фильтрация Телеграма и удаление битых ссылок.")

    # ШАГ 1: Сбор данных (Fetcher)
    # Fetcher берет список из sources.txt (где у тебя ссылки на ТГ и прочее)
    print("\n--- Шаг 1: Загрузка данных по списку из sources.txt ---")
    fetcher = ConfigFetcher()
    fetcher.fetch_all() 

    # ШАГ 2: Парсинг и конвертация
    # Собираем всё, что скачали, и добавляем то, что ты оставил в cleaned_urls.txt
    input_files = [raw_path]
    if os.path.exists(cleaned_file):
        print(f"🔗 Подключаю проверенные данные из cleaned_urls.txt")
        input_files.append(cleaned_file)

    print("\n--- Шаг 2: Извлечение конфигов и DNS ---")
    parser = FormatConverter(input_files=input_files, output_dir=unique_dir)
    parser.process()

    # ШАГ 3: Дедупликация
    # Здесь удаляются повторы, если одна и та же ссылка попала и в sources, и в cleaned
    print("\n--- Шаг 3: Удаление дубликатов ---")
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    # ШАГ 4: Валидация (Тот самый момент истины)
    # Всё, что выдает 404 или не пингуется, здесь СДОХНЕТ и не попадет в all_valid.txt
    print("\n--- Шаг 4: Финальная проверка (Удаление нерабочих) ---")
    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    print("\n✅ Цикл завершен. Все битые ссылки (404 и мертвые прокси) отсеяны!")

if __name__ == "__main__":
    main()
