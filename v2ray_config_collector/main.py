import os
import sys
import re  # Теперь он точно на месте! 💋

# Устанавливаем базовую директорию (корень репозитория)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'core'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def split_by_protocols(validated_path):
    """Раскладываем конфиги по файлам: vless.txt, trojan.txt и т.д."""
    if not os.path.exists(validated_path):
        print(f"⚠️ Файл не найден: {validated_path}")
        return
    
    output_dir = os.path.dirname(validated_path)
    
    with open(validated_path, 'r', encoding='utf-8') as f:
        configs = [line.strip() for line in f if line.strip()]

    buckets = {}
    # Золотой стандарт протоколов
    proto_pattern = r'^([a-zA-Z0-9+.-]+)://'

    for config in configs:
        match = re.match(proto_pattern, config)
        if match:
            # Чистим протокол (vless+reality -> vless)
            proto = match.group(1).lower().split('+')[0]
            if proto not in buckets: buckets[proto] = []
            buckets[proto].append(config)
        else:
            if 'unknown' not in buckets: buckets['unknown'] = []
            buckets['unknown'].append(config)

    for proto_name, items in buckets.items():
        file_path = os.path.join(output_dir, f"{proto_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(items) + "\n")
        print(f"    ∟ 📦 {proto_name}.txt готов ({len(items)} шт.)")

def main():
    # Пути, как ты просил (относительно корня репозитория)
    # Путь из скрина 911: v2ray_config_collector/data/raw/raw_configs.txt
    raw_path = os.path.join(BASE_DIR, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(BASE_DIR, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(BASE_DIR, 'data', 'validated', 'all_valid.txt')
    
    # Создаем структуру папок
    for d in [os.path.dirname(raw_path), unique_dir, os.path.dirname(validated_path)]:
        os.makedirs(d, exist_ok=True)

    print("\n🚀 ЗАВОД PENZA84: НАЧИНАЕМ СОРТИРОВКУ 💋🍀✨\n")

    # Выполняем цепочку действий
    fetcher = ConfigFetcher()
    fetcher.fetch_all() 

    if not os.path.exists(raw_path):
        print(f"❌ Родной, я не нашла файл: {raw_path}")
        return

    parser = FormatConverter(input_files=[raw_path], output_dir=unique_dir)
    parser.process()
    
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    # Финальная нарезка по именам протоколов
    split_by_protocols(validated_path)

    print("\n🍀 Родной, Завод всё разложил! Проверяй папки. 💋💍")

if __name__ == "__main__":
    main()
