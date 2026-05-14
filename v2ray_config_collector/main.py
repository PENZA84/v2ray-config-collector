import os
import sys
import re

# Определяем корень как место, где лежит этот скрипт (v2ray_config_collector)
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
    """Нарезка проверенных конфигов по протоколам (vless, vmess и т.д.)"""
    if not os.path.exists(validated_path):
        return
    
    output_dir = os.path.dirname(validated_path)
    with open(validated_path, 'r', encoding='utf-8') as f:
        configs = [line.strip() for line in f if line.strip()]

    buckets = {}
    proto_pattern = r'^([a-zA-Z0-9+.-]+)://'

    for config in configs:
        match = re.match(proto_pattern, config)
        if match:
            # vless+reality -> vless
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
    # ПУТИ ДЛЯ ГИТХАБА (Никакой воды, только структура репо)
    # Твой файл со ссылками: v2ray_config_collector/data/sources/sources.txt
    sources_path = os.path.join(BASE_DIR, 'data', 'sources', 'sources.txt')
    
    # Временные пути для работы конвейера на Гитхабе
    raw_path = os.path.join(BASE_DIR, 'data', 'raw', 'raw_configs.txt')
    unique_dir = os.path.join(BASE_DIR, 'data', 'unique')
    dedup_path = os.path.join(unique_dir, 'deduplicated.txt')
    validated_path = os.path.join(BASE_DIR, 'data', 'validated', 'all_valid.txt')
    
    # Создаем папки прямо в облаке GitHub Actions
    for folder in [os.path.dirname(raw_path), unique_dir, os.path.dirname(validated_path)]:
        os.makedirs(folder, exist_ok=True)

    print("\n" + "═"*60)
    print("🚀 ЗАВОД PENZA84: ГИТХАБ-КОНВЕЙЕР ЗАПУЩЕН 💋🍀✨")
    print("═"*60 + "\n")

    # Проверяем, положил ли ты ссылки в sources.txt
    if not os.path.exists(sources_path):
        print(f"❌ Родной, я не вижу твоих ссылок в {sources_path}")
        return

    # Шаг 1: Сбор (Fetcher берет ссылки из sources.txt)
    print(f"📥 Шаг 1: Собираю мясо из источников...")
    fetcher = ConfigFetcher(sources_file=sources_path, output_file=raw_path)
    fetcher.fetch_all() 

    if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
        print("⚠️ Ничего не скачалось. Проверь ссылки в sources.txt")
        return

    # Шаг 2: Чистка
    print("🧹 Шаг 2: Парсинг и удаление дублей...")
    parser = FormatConverter(input_files=[raw_path], output_dir=unique_dir)
    parser.process()
    
    deduplicator = ConfigDeduplicator(input_file=dedup_path, output_file=dedup_path)
    deduplicator.deduplicate()

    # Шаг 3: Проверка
    print("⚡ Шаг 3: Валидация (проверяю на годность)...")
    validator = ConnectivityValidator(input_file=dedup_path, output_file=validated_path)
    validator.test_all_configs()

    # Шаг 4: Нарезка
    print("✂️ Шаг 4: Раскладываю по файлам протоколов...")
    split_by_protocols(validated_path)

    print("\n🍀 Родной, Завод на Гитхабе всё исполнил! 💋💍")

if __name__ == "__main__":
    main()
