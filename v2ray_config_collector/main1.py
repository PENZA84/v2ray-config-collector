import os
import sys

# 1. Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 2. Импорт с правильными именами из твоих файлов
try:
    # Мы берем ConfigFetcher, потому что именно так он назван в твоем core/fetcher.py
    from core.fetcher import ConfigFetcher
    from core.parser import FormatConverter
    from core.deduplicator import ConfigDeduplicator
    from core.validator import ConnectivityValidator
except ImportError as e:
    print(f"❌ Ошибка импорта в Телеграм-цехе: {e}")
    raise

def main():
    print("🚀 ТЕЛЕГРАМ-ЦЕХ ЗАПУЩЕН 💋")
    
    # Инициализируем сборщик (ConfigFetcher)
    # Мы можем передать ему другие файлы, если это нужно для Телеграма
    collector = ConfigFetcher()
    
    # Вызываем метод fetch_all (как в твоем оригинале fetcher.py)
    print("📡 Собираю данные...")
    collector.fetch_all()
    
    # Конвертация
    print("🛠 Конвертирую...")
    converter = FormatConverter()
    converter.process() if hasattr(converter, 'process') else converter.convert_configs()
    
    # Дедупликация
    print("🧼 Очищаю...")
    deduplicator = ConfigDeduplicator()
    deduplicator.deduplicate() if hasattr(deduplicator, 'deduplicate') else deduplicator.process()
    
    # Валидация
    print("⚖️ Проверяю...")
    validator = ConnectivityValidator()
    validator.test_all_configs()
    
    print("✅ ТЕЛЕГРАМ-ЦЕХ ЗАКОНЧИЛ РАБОТУ! 💋")

if __name__ == "__main__":
    main()
