import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

try:
    from core.fetcher import SourceCollector
    from core.parser import FormatConverter
    from core.deduplicator import ConfigDeduplicator
    from core.validator import ConnectivityValidator
except ImportError as e:
    raise

def main():
    print("🚀 ТЕЛЕГРАМ-ЦЕХ ЗАПУЩЕН")
    
    # Здесь используем те же инструменты, что и в основном оригинале
    collector = SourceCollector()
    collector.fetch_all_configs()
    
    converter = FormatConverter()
    converter.convert_configs()
    
    deduplicator = ConfigDeduplicator()
    deduplicator.process()
    
    validator = ConnectivityValidator()
    validator.test_all_configs()
    print("✅ ТЕЛЕГРАМ-ЦЕХ ЗАКОНЧИЛ")

if __name__ == "__main__":
    main()
