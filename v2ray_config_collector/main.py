import os
import sys

# Настройка путей, чтобы Питон видел папку Ядро
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'Ядро'))

try:
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator
except ImportError as e:
    # Запасной путь для GitHub Actions
    sys.path.append(os.path.join(os.getcwd(), 'v2ray_config_collector', 'Ядро'))
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator

def main():
    print("🚀 ОСНОВНОЙ ЦЕХ ЗАПУЩЕН 💋")
    
    src = os.path.join(BASE_DIR, 'данные', 'источники', 'sources.txt')
    raw = os.path.join(BASE_DIR, 'данные', 'raw', 'raw.txt')
    unique_dir = os.path.join(BASE_DIR, 'данные', 'unique')
    valid_file = os.path.join(BASE_DIR, 'данные', 'validated', 'all_valid.txt')

    os.makedirs(unique_dir, exist_ok=True)

    # 1. Сбор
    ConfigFetcher(sources_file=src, output_file=raw).fetch_all()
    
    if os.path.exists(raw) and os.path.getsize(raw) > 0:
        # 2. Парсинг
        FormatConverter(input_files=[raw], output_dir=unique_dir).process()
        # 3. Дедупликация
        dedup = os.path.join(unique_dir, 'deduplicated.txt')
        ConfigDeduplicator(input_file=dedup, output_file=dedup).deduplicate()
        # 4. Валидация
        ConnectivityValidator(input_file=dedup, output_file=valid_file).test_all_configs()
        print("✅ Основной цех завершил работу успешно!")

if __name__ == "__main__":
    main()
