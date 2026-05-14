import os
import sys
import re
import shutil

# Устанавливаем базу относительно этого скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'core'))

try:
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")

def split_by_protocols(validated_path):
    """Нарезка конфигов. Чистим папку перед созданием новых файлов."""
    if not os.path.exists(validated_path):
        return
    
    output_dir = os.path.dirname(validated_path)
    
    # УДАЛЯЕМ старые файлы протоколов, чтобы нарезка была свежей
    for f in os.listdir(output_dir):
        if f.endswith('.txt') and f != 'all_valid.txt':
            os.remove(os.path.join(output_dir, f))

    with open(validated_path, 'r', encoding='utf-8') as f:
        configs = [line.strip() for line in f if line.strip()]

    buckets = {}
    proto_pattern = r'^([a-zA-Z0-9+.-]+)://'

    for config in configs:
        match = re.match(proto_pattern, config)
        if match:
            proto = match.group(1).lower().split('+')[0]
            if proto not in buckets: buckets[proto] = []
            buckets[proto].append(config)

    print(f"✂️ Нарезка файлов в: {output_dir}")
    for proto_name, items in buckets.items():
        file_path = os.path.join(output_dir, f"{proto_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(items) + "\n")
        print(f"    ∟ ✅ {proto_name}.txt готов ({len(items)} шт.)")

def main():
    # ПУТИ ДЛЯ ГИТХАБА (всё внутри структуры репо)
    sources_path = os.path.join(BASE_DIR, 'data', 'sources', 'sources.txt')
    raw_path = os.path.join(BASE_DIR, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(BASE_DIR, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(BASE_DIR, 'data', 'validated', 'all_valid.txt')
    
    # Создаем структуру папок на лету
    for folder in [os.path.dirname(raw_path), unique_dir, os.path.dirname(validated_path)]:
        os.makedirs(folder, exist_ok=True)

    print("\n🚀 ЗАВОД PENZA84: ГИТХАБ-КОНВЕЙЕР ЗАПУЩЕН 💋🍀")

    if not os.path.exists(sources_path):
        print(f"❌ Родной, я не вижу источников в {sources_path}")
        return

    # 1. Сбор
    fetcher = ConfigFetcher(sources_file=sources_path, output_file=raw_path)
    fetcher.fetch_all() 

    if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
        print("⚠️ Пусто в баке. Проверь sources.txt")
        return

    # 2. Обработка
    parser = FormatConverter(input_files=[raw_path], output_dir=unique_dir)
    parser.process()
    
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    # 3. Валидация
    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    # 4. Нарезка
    split_by_protocols(validated_path)

    print("\n🍀 Родной, всё готово! 💋💍")

if __name__ == "__main__":
    main()
