import os
import sys

# 1. НАСТРОЙКА ПУТЕЙ (Чтобы Питон видел папку core)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 2. ИМПОРТ ИЗ ТВОИХ РЕАЛЬНЫХ ФАЙЛОВ
try:
    # Импортируем именно те имена, которые в твоих файлах
    from core.fetcher import ConfigFetcher
    from core.parser import FormatConverter
    from core.deduplicator import ConfigDeduplicator
    from core.validator import ConnectivityValidator
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"Проверь, что в папке {BASE_DIR}/core есть файлы fetcher.py, parser.py и т.д.")
    raise

def main():
    print("🚀 СЕМЕЙНЫЙ ЗАВОД: ОСНОВНОЙ ЦЕХ ЗАПУЩЕН 💋")
    
    # Создаем папки для данных, если Гитхаб их еще не видит
    data_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(os.path.join(data_dir, 'raw'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'validated'), exist_ok=True)

    # 1. СБОР (Используем твои реальные методы)
    print("📡 Начинаю сбор конфигов...")
    collector = ConfigFetcher()
    collector.fetch_all()
    
    # 2. КОНВЕРТАЦИЯ
    print("🛠 Конвертация форматов...")
    converter = FormatConverter()
    # Если метод называется иначе, он попробует оба варианта
    converter.process() if hasattr(converter, 'process') else converter.convert_configs()
    
    # 3. ОЧИСТКА ДУБЛИКАТОВ
    print("🧼 Удаление дубликатов...")
    dedup = ConfigDeduplicator()
    dedup.deduplicate() if hasattr(dedup, 'deduplicate') else dedup.process()
    
    # 4. ПРОВЕРКА (ВАЛИДАЦИЯ)
    print("⚖️ Проверка соединений...")
    validator = ConnectivityValidator()
    validator.test_all_configs()
    
    print("✅ ОСНОВНОЙ ЦЕХ ЗАКОНЧИЛ РАБОТУ! 🏆")

if __name__ == "__main__":
    main()
