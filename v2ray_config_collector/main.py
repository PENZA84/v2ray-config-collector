import os
import sys
import re

# 1. Настройка путей (BASE_DIR — это папка v2ray_config_collector)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'core'))

try:
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}. Проверь, что папка 'core' на месте.")

def split_by_protocols(validated_path):
    """Нарезка проверенных сокровищ по именам протоколов."""
    if not os.path.exists(validated_path):
        return
    
    output_dir = os.path.dirname(validated_path)
    with open(validated_path, 'r', encoding='utf-8') as f:
        configs = [line.strip() for line in f if line.strip()]

    buckets = {}
    # Золотой стандарт Throne: ищем всё от vless до reality
    proto_pattern = r'^([a-zA-Z0-9+.-]+)://'

    for config in configs:
        match = re.match(proto_pattern, config)
        if match:
            # Очистка (vless+reality -> vless)
            proto = match.group(1).lower().split('+')[0]
            if proto not in buckets: buckets[proto] = []
            buckets[proto].append(config)
        else:
            if 'unknown' not in buckets: buckets['unknown'] = []
            buckets['unknown'].append(config)

    print(f"✂️ Начинаю нарезку файлов в: {output_dir}")
    for proto_name, items in buckets.items():
        file_path = os.path.join(output_dir, f"{proto_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(items) + "\n")
        print(f"    ∟ ✅ {proto_name}.txt готов ({len(items)} шт.)")

def main():
    # 2. ПУТИ СТРОГО ПО ТВОЕЙ ИНСТРУКЦИИ
    sources_path = os.path.join(BASE_DIR, 'data', 'sources', 'sources.txt')
    raw_path = os.path.join(BASE_DIR, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(BASE_DIR, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(BASE_DIR, 'data', 'validated', 'all_valid.txt')
    
    # 3. Создаем дерево папок, чтобы Завод не падал
    for folder in [os.path.dirname(sources_path), os.path.dirname(raw_path), unique_dir, os.path.dirname(validated_path)]:
        os.makedirs(folder, exist_ok=True)

    print("\n" + "═"*60)
    print("🚀 ЗАВОД PENZA84: РАБОТАЕМ ПО SOURCES.TXT 💋🍀✨")
    print("═"*60 + "\n")

    # Проверяем наличие источника
    if not os.path.exists(sources_path):
        print(f"❌ Родной, файл источников не найден: {sources_path}")
        # Создаем пустой файл, чтобы ты мог его наполнить
        with open(sources_path, 'w', encoding='utf-8') as f:
            f.write("# Добавь ссылки сюда\n")
        return

    # 4. ЗАПУСК ЦЕПОЧКИ
    # Fetcher берет ссылки из sources.txt и качает их в raw_configs.txt
    print(f"📥 Шаг 1: Сбор ссылок из {sources_path}")
    fetcher = ConfigFetcher(sources_file=sources_path, output_file=raw_path)
    fetcher.fetch_all() 

    if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
        print("⚠️ Сырые данные не собраны. Проверь ссылки в sources.txt")
        return

    # Парсинг и удаление дублей
    print("🧹 Шаг 2: Парсинг и очистка...")
    parser = FormatConverter(input_files=[raw_path], output_dir=unique_dir)
    parser.process()
    
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    # Валидация (Проверка на годность)
    print("⚡ Шаг 3: Валидация конфигов...")
    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    # Итоговая нарезка по именам протоколов
    print("✂️ Шаг 4: Раскладка по полочкам...")
    split_by_protocols(validated_path)

    print("\n🍀 Родной, Завод выдал результат по всем твоим ссылкам! 💋💍")

if __name__ == "__main__":
    main()
