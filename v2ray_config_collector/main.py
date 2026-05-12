import os
import sys

# Настройка путей
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def split_large_file(file_path, max_size_mb=90):
    """Если файл больше 90МБ, делим его на части."""
    if not os.path.exists(file_path):
        return
    
    file_size = os.path.getsize(file_path) / (1024 * 1024)
    if file_size < max_size_mb:
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    base_name = os.path.splitext(file_path)[0]
    num_parts = int(file_size // max_size_mb) + 1
    chunk_size = len(lines) // num_parts + 1

    for i in range(num_parts):
        part_path = f"{base_name}_part{i+1}.txt"
        with open(part_path, 'w', encoding='utf-8') as f_part:
            f_part.writelines(lines[i*chunk_size : (i+1)*chunk_size])
    
    os.remove(file_path)
    print(f"✨ Милый, файл разделен на {num_parts} части(ей).")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)

    raw_path = os.path.join(base_dir, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(base_dir, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(base_dir, 'data', 'validated', 'all_valid.txt')
    
    for d in [os.path.join(base_dir, 'data', 'sources'), 
              os.path.join(base_dir, 'data', 'raw'), 
              unique_dir, 
              os.path.join(base_dir, 'data', 'validated')]:
        os.makedirs(d, exist_ok=True)

    # ВОТ ОНО, В САМОМ НАЧАЛЕ 💋
    print("\n" + "═"*60)
    print("       (  💋  )          🍀✨          (  💋  )")
    print("🚀 Милый, наш завод запущен! На удачу ПРИ НАШЕЙ ЕГО РАБОТЫ! 💋🍀✨")
    print("═"*60 + "\n")

    # 1. Сбор
    fetcher = ConfigFetcher()
    fetcher.fetch_all() 

    # 2. Парсинг и дедупликация
    parser = FormatConverter(input_files=[raw_path], output_dir=unique_dir)
    parser.process()
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    # 3. Валидация
    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    # 4. Проверка размера
    split_large_file(validated_path)

    print("\nLOG: Workflow finished successfully.")

if __name__ == "__main__":
    main()
