import os
import sys

# Гарантируем, что Python видит папку core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.fetcher import SourceCollector
from core.parser import FormatConverter
from core.deduplicator import ConfigDeduplicator
from core.validator import ConnectivityValidator

def main():
    title1 = "V2Ray Config Collector"
    print(f"\n{title1}")
    print("=" * len(title1))
    
    # 1. Собираем сырые данные из источников
    collector = SourceCollector()
    collector.fetch_all_configs()
    
    title2 = "Deep Parsing (JSON, YAML, Base64, DNS)"
    print(f"\n{title2}")
    print("=" * len(title2))
    # Создаем конвертер и запускаем процесс
    converter = FormatConverter()
    # ВАЖНО: используем метод process(), который мы прописали в новом parser.py
    converter.process()
    
    title3 = "Deduplication & Cleaning"
    print(f"\n{title3}")
    print("=" * len(title3))
    # Дедупликатор берет файл deduplicated.txt и чистит его
    deduplicator = ConfigDeduplicator()
    deduplicator.process()
    
    title4 = "Connectivity Validation"
    print(f"\n{title4}")
    print("=" * len(title4))
    # Валидатор проверяет, какие из прокси реально дышат
    validator = ConnectivityValidator()
    validator.test_all_configs()

    print("\n" + "="*30)
    print("Сбор и проверка завершены!")
    print("="*30)

if __name__ == "__main__":
    main()
