import os
import sys

# Настройка путей, чтобы код видел папку Ядро
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'Ядро'))

try:
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator
except ImportError:
    # Запасной путь для GitHub Actions
    sys.path.append(os.path.join(os.getcwd(), 'v2ray_config_collector', 'Ядро'))
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator

def split_telegram(valid_file):
    if not os.path.exists(valid_file):
        return
    output_dir = os.path.dirname(valid_file)
    with open(valid_file, 'r', encoding='utf-8') as f:
        configs = [l.strip() for l in f if l.strip()]

    buckets = {}
    for c in configs:
        try:
            proto = c.split('://')[0].lower().split('+')[0]
            if proto not in buckets:
                buckets[proto] = []
            # Добавляем метку источника
            labeled = c + "_tg" if '#' in c else c + "#tg"
            buckets[proto].append(labeled)
        except:
            continue

    for proto, items in buckets.items():
        file_path = os.path.join(output_dir, f"{proto}_tg.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(items) + "\n")
        print(f"DONE: {proto}_tg.txt created")

def main():
    print("START TELEGRAM PROCESS")
    data_dir = os.path.join(BASE_DIR, 'данные')
    src = os.path.join(data_dir, 'источники', 'sources1.txt')
    raw = os.path.join(data_dir, 'raw', 'raw_tg.txt')
    unique_dir = os.path.join(data_dir, 'unique_tg')
    valid_file = os.path.join(data_dir, 'validated', 'all_valid_tg.txt')

    if not os.path.exists(unique_dir):
        os.makedirs(unique_dir, exist_ok=True)

    # 1. Сбор
    ConfigFetcher(sources_file=src, output_file=raw).fetch_all()
    
    if os.path.exists(raw) and os.path.getsize(raw) > 0:
        # 2. Парсинг
        FormatConverter(input_files=[raw], output_dir=unique_dir).process()
        # 3. Дедупликация
        dedup = os.path.join(unique_dir, 'deduplicated.txt')
        if os.path.exists(dedup):
            ConfigDeduplicator(input_file=dedup, output_file=dedup).deduplicate()
            # 4. Валидация
            ConnectivityValidator(input_file=dedup, output_file=valid_file).test_all_configs()
            # 5. Нарезка
            split_telegram(valid_file)
            print("FINISH TELEGRAM SUCCESS")
    else:
        print("NO DATA FOUND IN SOURCES1")

if __name__ == "__main__":
    main()
