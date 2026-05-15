import os
import sys

# Получаем абсолютный путь к папке, где лежит этот файл (main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Четко указываем путь к папке Ядро, которая лежит рядом
CORE_PATH = os.path.join(BASE_DIR, 'Ядро')

# Добавляем в систему поиска Питона
if CORE_PATH not in sys.path:
    sys.path.insert(0, CORE_PATH)
    sys.path.insert(0, BASE_DIR)

try:
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator
except ImportError as e:
    print(f"CRITICAL ERROR: {e}")
    print(f"I am here: {BASE_DIR}")
    print(f"Looking for core in: {CORE_PATH}")
    raise

def main():
    print("START MAIN PROCESS")
    
    # Пути к данным внутри твоей папки
    data_dir = os.path.join(BASE_DIR, 'данные')
    src = os.path.join(data_dir, 'источники', 'sources.txt')
    raw = os.path.join(data_dir, 'raw', 'raw.txt')
    unique_dir = os.path.join(data_dir, 'unique')
    valid_file = os.path.join(data_dir, 'validated', 'all_valid.txt')

    os.makedirs(unique_dir, exist_ok=True)
    os.makedirs(os.path.dirname(valid_file), exist_ok=True)

    ConfigFetcher(sources_file=src, output_file=raw).fetch_all()
    
    if os.path.exists(raw) and os.path.getsize(raw) > 0:
        FormatConverter(input_files=[raw], output_dir=unique_dir).process()
        dedup = os.path.join(unique_dir, 'deduplicated.txt')
        if os.path.exists(dedup):
            ConfigDeduplicator(input_file=dedup, output_file=dedup).deduplicate()
            ConnectivityValidator(input_file=dedup, output_file=valid_file).test_all_configs()
            print("FINISH SUCCESS")

if __name__ == "__main__":
    main()
