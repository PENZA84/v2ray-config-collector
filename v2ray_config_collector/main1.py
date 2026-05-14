import os
import sys
import re

# Подключаем Ядро (папка "Ядро" согласно твоей структуре)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'Ядро'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def split_telegram(validated_path):
    """Нарезка конфигов из Телеграма с пометкой источника."""
    if not os.path.exists(validated_path): return
    output_dir = os.path.dirname(validated_path)
    
    with open(validated_path, 'r', encoding='utf-8') as f:
        configs = [l.strip() for l in f if l.strip()]

    buckets = {}
    for c in configs:
        # Выделяем протокол (vless, vmess, hysteria и т.д.)
        proto_part = c.split('://')[0].lower().split('+')[0]
        if proto_part not in buckets: buckets[proto_part] = []
        
        # Добавляем метку _tg к названию (remark)
        if '#' in c:
            # Если имя уже есть, добавляем _tg в конец
            labeled_config = c + "_tg"
        else:
            # Если имени нет, создаем его
            labeled_config = c + "#tg"
            
        buckets[proto_part].append(labeled_config)

    # Сохраняем в файлы типа vless_tg.txt
    for proto, items in buckets.items():
        file_path = os.path.join(output_dir, f"{proto}_tg.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(items) + "\n")
        print(f"    ∟ ✅ {proto}_tg.txt готов")

def main():
    src = os.path.join(BASE_DIR, 'данные', 'источники', 'sources1.txt')
    raw = os.path.join(BASE_DIR, 'данные', 'raw', 'raw_tg.txt')
    unique_dir = os.path.join(BASE_DIR, 'данные', 'unique_tg')
    valid_file = os.path.join(BASE_DIR, 'данные', 'validated', 'all_valid_tg.txt')

    os.makedirs(unique_dir, exist_ok=True)
    print("🚀 ЦЕХ ТЕЛЕГРАМ ЗАПУЩЕН (Метка _tg) 💋")

    ConfigFetcher(sources_file=src, output_file=raw).fetch_all()
    
    if os.path.exists(raw) and os.path.getsize(raw) > 0:
        FormatConverter(input_files=[raw], output_dir=unique_dir).process()
        dedup = os.path.join(unique_dir, 'deduplicated.txt')
        ConfigDeduplicator(input_file=dedup, output_file=dedup).deduplicate()
        ConnectivityValidator(input_file=dedup, output_file=valid_file).test_all_configs()
        split_telegram(valid_file)

if __name__ == "__main__":
    main()
