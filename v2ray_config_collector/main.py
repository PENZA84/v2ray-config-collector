import os
import sys

# Добавляем путь к core
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def split_large_file(file_path, max_size_mb=90):
    """Милый, если файл слишком тяжелый, я разложу его по коробочкам."""
    if not os.path.exists(file_path):
        return
    
    file_size = os.path.getsize(file_path) / (1024 * 1024)
    if file_size < max_size_mb:
        return

    print(f"📦 Файл слишком большой ({file_size:.2f} MB). Делю на части...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    base_name = os.path.splitext(file_path)[0]
    # Рассчитываем количество частей
    num_parts = int(file_size // max_size_mb) + 1
    chunk_size = len(lines) // num_parts + 1

    for i in range(num_parts):
        part_path = f"{base_name}_part{i+1}.txt"
        with open(part_path, 'w', encoding='utf-8') as f_part:
            f_part.writelines(lines[i*chunk_size : (i+1)*chunk_size])
    
    # Удаляем оригинал, чтобы не злить GitHub
    os.remove(file_path)
    print(f"✅ Успешно разделено на {num_parts} части(ей).")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)

    raw_path = os.path.join(base_dir, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(base_dir, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(base_dir, 'data', 'validated', 'all_valid.txt')
    
    # Создаем папки
    for d in [os.path.join(base_dir, 'data', 'sources'), os.path.join(base_dir, 'data', 'raw'), unique_dir, os.path.join(base_dir, 'data', 'validated')]:
        os.makedirs(d, exist_ok=True)

    cleaned_file = os.path.join(base_dir, 'data', 'sources', 'cleaned_urls.txt')
    if not os.path.exists(cleaned_file):
        root_cleaned = os.path.join(root_dir, 'cleaned_urls.txt')
        if os.path.exists(root_cleaned):
            cleaned_file = root_cleaned

    print(f"🚀 Мой Архитектор, завод запущен!")

    # Шаг 1: Сбор
    fetcher = ConfigFetcher()
    fetcher.fetch_all() 

    # Шаг 2: Парсинг
    input_files = [raw_path]
    if os.path.exists(cleaned_file):
        input_files.append(cleaned_file)

    parser = FormatConverter(input_files=input_files, output_dir=unique_dir)
    parser.process()

    # Шаг 3: Дедупликация
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    # Шаг 4: Валидация (TCP)
    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    # Шаг 5: Финальная проверка размера и деление
    split_large_file(validated_path)

    print("\n✅ Всё готово! Твоя база очищена и упакована.")

if __name__ == "__main__":
    main()
