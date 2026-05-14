import os
import sys
import re

# Подключаем Ядро
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'Ядро'))

from fetcher import ConfigFetcher
from parser import FormatConverter
from deduplicator import ConfigDeduplicator
from validator import ConnectivityValidator

def split_standard(validated_path):
    """Нарезка только стандартных протоколов из глобальных источников."""
    if not os.path.exists(validated_path): return
    output_dir = os.path.dirname(validated_path)
    
    # Чистим старье (только файлы без приставки _tg)
    for f in os.listdir(output_dir):
        if f.endswith('.txt') and not f.endswith('_tg.txt') and f != 'all_valid.txt':
            os.remove(os.path.join(output_dir, f))

    with open(validated_path, 'r', encoding='utf-8') as f:
        configs = [l.strip() for l in f if l.strip()]

    buckets = {}
    for c in configs:
        proto = c.split('://')[0].lower().split('+')[0]
        if proto not in buckets: buckets[proto] = []
        buckets[proto].append(c)

    for proto, items in buckets.items():
        with open(os.path.join(output_dir, f"{proto}.txt"), 'w', encoding='utf-8') as f:
            f.write("\n".join(items) + "\n")
        print(f"    ∟ ✅ {proto}.txt готов ({len(items)} шт.)")

def main():
    src = os.path.join(BASE_DIR, 'данные', 'источники', 'sources.txt')
    raw = os.path.join(BASE_DIR, 'данные', 'raw', 'raw_web.txt')
    unique_dir = os.path.join(BASE_DIR, 'данные', 'unique')
    valid_file = os.path.join(BASE_DIR, 'данные', 'validated', 'all_valid.txt')

    os.makedirs(unique_dir, exist_ok=True)
    print("🚀 ЦЕХ ГЛОБАЛ (WEB) ЗАПУЩЕН 💋")

    ConfigFetcher(sources_file=src, output_file=raw).fetch_all()
    
    if os.path.exists(raw) and os.path.getsize(raw) > 0:
        FormatConverter(input_files=[raw], output_dir=unique_dir).process()
        dedup = os.path.join(unique_dir, 'deduplicated.txt')
        ConfigDeduplicator(input_file=dedup, output_file=dedup).deduplicate()
        ConnectivityValidator(input_file=dedup, output_file=valid_file).test_all_configs()
        split_standard(valid_file)

if __name__ == "__main__":
    main()
