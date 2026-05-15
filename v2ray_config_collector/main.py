import os
import sys

# 1. НАСТРОЙКА ПУТЕЙ (Чтобы Питон видел папку core)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Добавляем саму папку проекта в поиск Питона
sys.path.insert(0, BASE_DIR)

# Пытаемся импортировать модули из папки core
try:
    from core.fetcher import SourceCollector
    from core.parser import FormatConverter
    from core.deduplicator import ConfigDeduplicator
    from core.validator import ConnectivityValidator
except ImportError as e:
    print(f"ОШИБКА ИМПОРТА: {e}")
    print(f"Я нахожусь в: {BASE_DIR}")
    print("Содержимое папки:", os.listdir(BASE_DIR))
    raise

def main():
    title1 = "V2Ray Config Collector"
    print(title1)
    print("=" * len(title1))
    
    # Сбор данных
    collector = SourceCollector()
    collector.fetch_all_configs()
    
    title2 = "Convert proxy configurations to JSON format"
    print(title2)
    print("=" * len(title2))
    converter = FormatConverter()
    converter.convert_configs()
    
    title3 = "Remove duplicate configurations"
    print(title3)
    print("=" * len(title3))
    deduplicator = ConfigDeduplicator()
    deduplicator.process()
    
    title4 = "Tests TCP connectivity of proxy configurations"
    print(title4)
    print("=" * len(title4))
    validator = ConnectivityValidator()
    validator.test_all_configs()
    print("✅ ВСЁ ГОТОВО, МОЙ РОДНОЙ!")

if __name__ == "__main__":
    main()
