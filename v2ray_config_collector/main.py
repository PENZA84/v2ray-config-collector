import os
import sys

# Эта строка гарантирует, что Python увидит папку core, 
# даже если запуск идет через GitHub Actions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.fetcher import SourceCollector
from core.parser import FormatConverter
from core.deduplicator import ConfigDeduplicator
from core.validator import ConnectivityValidator

def main():
    title1 = "V2Ray Config Collector"
    print(title1)
    print("=" * len(title1))
    
    # Создаем объект коллектора. 
    # Он сам пойдет в data/sources/sources.txt (мы это настроим в fetcher.py)
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
    success = deduplicator.process()
    
    title4 = "Tests TCP connectivity of proxy configurations"
    print(title4)
    print("=" * len(title4))
    validator = ConnectivityValidator()
    validator.test_all_configs()

if __name__ == "__main__":
    main()
