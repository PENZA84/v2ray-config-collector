import os
import sys
import re  # ГЛАВНЫЙ ИМПОРТ: Теперь всё будет четко! 💋

# Настройка путей
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_dir, 'core'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def split_by_protocols(validated_path):
    """Динамическая раскладка по файлам vless.txt, trojan.txt и т.д."""
    if not os.path.exists(validated_path):
        print(f"⚠️ Файл для нарезки не найден: {validated_path}")
        return
    
    base_dir = os.path.dirname(validated_path)
    with open(validated_path, 'r', encoding='utf-8') as f:
        configs = [line.strip() for line in f if line.strip()]

    buckets = {}
    # Наш золотой стандарт Throne-протоколов
    proto_pattern = r'^([a-zA-Z0-9+.-]+)://'

    for config in configs:
        match = re.match(proto_pattern, config)
        if match:
            proto = match.group(1).lower().split('+')[0]
            if proto not in buckets: buckets[proto] = []
            buckets[proto].append(config)
        else:
            if 'unknown' not in buckets: buckets['unknown'] = []
            buckets['unknown'].append(config)

    for proto_name, items in buckets.items():
        file_path = os.path.join(base_dir, f"{proto_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(items) + "\n")
        print(f"    ∟ 📦 {proto_name}.txt готов ({len(items)} шт.)")

def main():
    # Пути должны быть четкими, как твои инструкции
    raw_path = os.path.join(base_dir, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(base_dir, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(base_dir, 'data', 'validated', 'all_valid.txt')
    
    # Создаем папки
    for d in [os.path.dirname(raw_path), unique_dir, os.path.dirname(validated_path)]:
        os.makedirs(d, exist_ok=True)

    print("\n🚀 ЗАВОД PENZA84: ЗАПУСК ПРОИЗВОДСТВА 💋🍀✨\n")

    # 1. Сбор и обработка
    fetcher = ConfigFetcher()
    fetcher.fetch_all() 

    # Проверяем, скачалось ли хоть что-то
    if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
        print("❌ Родной, в баке пусто! Проверь источники.")
        return

    parser = FormatConverter(input_files=[raw_path], output_dir=unique_dir)
    parser.process()
    
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    # 2. Нарезка сокровищ
    split_by_protocols(validated_path)

    print("\n🍀 Родной, всё разложено по полочкам! Завод выполнил план. 💋💍")

if __name__ == "__main__":
    main()
