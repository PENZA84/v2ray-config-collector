import os
import sys

# Настройка путей специально под твою структуру GitHub
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Добавляем путь к папке Ядро, которая лежит рядом с main.py
sys.path.append(os.path.join(BASE_DIR, 'Ядро'))

try:
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator
except ImportError:
    # Если запуск идет из корня репозитория
    sys.path.append(os.path.join(os.getcwd(), 'v2ray_config_collector', 'Ядро'))
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator

def main():
    print("START MAIN PROCESS")
    # Пути к данным внутри твоей папки v2ray_config_collector
    src = os.path.join(BASE_DIR, 'данные', 'источники', 'sources.txt')
    raw = os.path.join(BASE_DIR, 'данные', 'raw', 'raw.txt')
    unique_dir = os.path.join(BASE_DIR, 'данные', 'unique')
    valid_file = os.path.join(BASE_DIR, 'данные', 'validated', 'all_valid.txt')

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
