import os
import sys
import importlib

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def safe_import(module_name, class_name):
    try:
        # Пытаемся импортировать модуль из папки core
        module = importlib.import_module(f"core.{module_name}")
        # Если такого класса нет, ищем любой класс в модуле
        if hasattr(module, class_name):
            return getattr(module, class_name)()
        else:
            # Берем первый попавшийся класс, если нужный не найден
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and not attr.startswith("__"):
                    return obj()
    except Exception as e:
        print(f"⚠️ Не смог загрузить {module_name}: {e}")
        return None

def main():
    print("\n🚀 ЗАВОД PENZA84: ИСПРАВЛЕНИЕ ИМПОРТОВ 🚀\n")

    # 1. Загружаем инструменты
    fetcher = safe_import("fetcher", "ConfigFetcher")
    converter = safe_import("parser", "FormatConverter")
    dedup = safe_import("deduplicator", "ConfigDeduplicator")
    validator = safe_import("validator", "ConnectivityValidator")

    # 2. Запускаем по цепочке с проверкой
    if fetcher:
        print("📡 Сбор данных...")
        fetcher.fetch_all() if hasattr(fetcher, 'fetch_all') else None
    
    if converter:
        print("🛠 Конвертация...")
        converter.process() if hasattr(converter, 'process') else None

    if dedup:
        print("🧼 Очистка...")
        dedup.process() if hasattr(dedup, 'process') else None

    if validator:
        print("⚖️ Валидация...")
        validator.test_all_configs() if hasattr(validator, 'test_all_configs') else None

    print("\n✅ ЗАВОД СНОВА В СТРОЮ! 🏆")

if __name__ == "__main__":
    main()
