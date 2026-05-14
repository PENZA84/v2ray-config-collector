import os
import sys

# Настройка путей
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def split_by_protocols(validated_path):
    """Динамическая раскладка: как называется протокол, так и назовем файл."""
    if not os.path.exists(validated_path):
        return
    
    base_dir = os.path.dirname(validated_path)
    
    with open(validated_path, 'r', encoding='utf-8') as f:
        configs = [line.strip() for line in f if line.strip()]

    # Словарь для сортировки: { 'vmess': ['link1', 'link2'], 'vless': [...] }
    buckets = {}

    print("✨ Милый, я включаю умную сортировку сокровищ...")

    for config in configs:
        # Ищем протокол (всё, что до ://)
        match = re.match(r'^([a-zA-Z0-9+.-]+)://', config)
        if match:
            proto = match.group(1).lower()
            # Убираем лишние детали, например naive+https -> naive
            clean_proto = proto.split('+')[0]
            
            if clean_proto not in buckets:
                buckets[clean_proto] = []
            buckets[clean_proto].append(config)
        else:
            # Если протокол не распознан, кладем в "неизвестное"
            if 'unknown' not in buckets:
                buckets['unknown'] = []
            buckets['unknown'].append(config)

    # Записываем каждый бакет в свой файл
    for proto_name, items in buckets.items():
        file_path = os.path.join(base_dir, f"{proto_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as f_proto:
            for item in items:
                f_proto.write(f"{item}\n")
        print(f"   ∟ 📦 {proto_name}.txt готов ({len(items)} шт.)")

def split_large_file(file_path, max_size_mb=90):
    """Делим ALL_valid, если он слишком тяжелый."""
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
    print(f"✨ Милый, огромный файл разделен на {num_parts} части(ей).")

def main():
    import re # Импорт здесь для работы функции split
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Пути
    raw_path = os.path.join(base_dir, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(base_dir, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(base_dir, 'data', 'validated', 'all_valid.txt')
    
    # Создаем структуру
    for d in [os.path.join(base_dir, 'data', 'sources'), 
              os.path.join(base_dir, 'data', 'raw'), 
              unique_dir, 
              os.path.join(base_dir, 'data', 'validated')]:
        os.makedirs(d, exist_ok=True)

    print("\n" + "═"*60)
    print("        (  💋  )           🍀✨           (  💋  )")
    print("🚀 Милый, ЗАВОД РАБОТАЕТ! Раскладываем всё по именам! 💋🍀✨")
    print("═"*60 + "\n")

    # 1. Работа ядра
    fetcher = ConfigFetcher()
    fetcher.fetch_all() 

    parser = FormatConverter(input_files=[raw_path], output_dir=unique_dir)
    parser.process()
    
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    # 2. Твоя Умная Нарезка 💋
    split_by_protocols(validated_path)

    # 3. Финальный штрих
    split_large_file(validated_path)

    print("\n🍀 Родной, всё разложено по полочкам. Никакой кучи, только порядок! 💋💍")

if __name__ == "__main__":
    main()
