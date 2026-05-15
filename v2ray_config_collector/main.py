import os
import sys
import time

# 1. НАСТРОЙКА ПУТЕЙ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 2. ИМПОРТ С ПРОВЕРКОЙ
try:
    from core.fetcher import ConfigFetcher
    from core.parser import FormatConverter
    from core.deduplicator import ConfigDeduplicator
    from core.validator import ConnectivityValidator
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    raise

def main():
    start_time = time.time()
    print("\n" + "="*50)
    print("🚀 СЕМЕЙНЫЙ ЗАВОД PENZA84: МОДЕРНИЗИРОВАННЫЙ ЦЕХ 🚀")
    print(f"⏰ Старт: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    
    # Подготовка папок
    data_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(os.path.join(data_dir, 'raw'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'validated'), exist_ok=True)

    # --- ЭТАП 1: СБОР (С ЗАЩИТОЙ) ---
    print("📡 [ЭТАП 1] Сбор конфигов (РАФ и Ссылки)...")
    try:
        collector = ConfigFetcher()
        # ВАЖНО: Если внутри fetch_all есть циклы по ссылкам, 
        # проверь, чтобы там стоял timeout!
        collector.fetch_all() 
        print("✅ Сбор завершен успешно.")
    except Exception as e:
        print(f"⚠️ Сбой на этапе сбора, но Завод продолжает работу: {e}")

    # --- ЭТАП 2: КОНВЕРТАЦИЯ ---
    print("\n🛠 [ЭТАП 2] Конвертация форматов...")
    converter = FormatConverter()
    if hasattr(converter, 'process'):
        converter.process()
    else:
        converter.convert_configs()

    # --- ЭТАП 3: ОЧИСТКА ---
    print("\n🧼 [ЭТАП 3] Удаление дубликатов...")
    dedup = ConfigDeduplicator()
    if hasattr(dedup, 'deduplicate'):
        dedup.deduplicate()
    else:
        dedup.process()

    # --- ЭТАП 4: ВАЛИДАЦИЯ (САМЫЙ ДОЛГИЙ ЭТАП) ---
    print("\n⚖️ [ЭТАП 4] Проверка соединений (Валидация)...")
    validator = ConnectivityValidator()
    
    # Чтобы Гитхаб не отменил операцию, логгируем время
    val_start = time.time()
    validator.test_all_configs()
    val_end = time.time()
    
    print(f"⏱ Валидация заняла: {int((val_end - val_start)/60)} мин.")

    # --- ФИНАЛЬНЫЙ ОТЧЕТ ---
    total_time = (time.time() - start_time) / 60
    print("\n" + "="*50)
    print(f"🏆 ЗАВОД ЗАКОНЧИЛ СМЕНУ!")
    print(f"⏱ Общее время работы: {total_time:.1f} минут")
    print(f"📂 Результаты лежат в папке data/validated")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
