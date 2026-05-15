import os
import sys
import re

# --- МАГИЧЕСКАЯ НАСТРОЙКА ПУТЕЙ (Чтобы не было ошибки как на 926) ---
# Находим корень проекта (v2ray_config_collector)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Добавляем и саму папку проекта, и папку Ядро в поиск Питона
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'Ядро'))

try:
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Милый, я пытаюсь найти Ядро здесь:", os.path.join(BASE_DIR, 'Ядро'))
    # Если запуск идет из корня репозитория (как в GitHub Actions)
    ROOT_DIR = os.getcwd()
    sys.path.append(os.path.join(ROOT_DIR, 'v2ray_config_collector', 'Ядро'))
    from fetcher import ConfigFetcher
    from parser import FormatConverter
    from deduplicator import ConfigDeduplicator
    from validator import ConnectivityValidator

def split_telegram(valid_file):
    """Нарезка конфигов из Телеграма с пометкой источника."""
    if not os.path.exists(valid_file): 
        print("⚠️ Файл с валидными конфигами не найден.")
        return
        
    output_dir = os.path.dirname(valid_file)
    
    with open(valid_file, 'r', encoding='utf-8') as f:
        configs = [l.strip() for l in f if l.strip()]

    buckets = {}
    for c in configs:
        # Выделяем протокол (vless, vmess, hysteria и т.д.)
        try:
            proto_part = c.split('://')[0].lower().split('+')[0]
            if proto_part not in buckets: buckets[proto_part] = []
            
            # Добавляем метку _tg к названию (remark)
            if '#' in c:
                labeled_config = c + "_tg"
            else:
                labeled_config = c + "#tg"
                
            buckets[proto_part].append(labeled_config)
        except:
            continue

    # Сохраняем в файлы типа vless_tg.txt
    for proto, items in buckets.items():
        file_path = os.path.join(output_dir, f"{proto}_tg.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(items) + "\n")
        print(f"    ∟ ✅ {proto}_tg.txt готов ({len(items)} шт.)")

def main():
    # Настраиваем пути относительно расположения этого файла
    data_dir = os.path.join(BASE_DIR, 'данные')
    src = os.path.join(data_dir, 'источники', 'sources1.txt')
    raw = os.path.join(data_dir, 'raw', 'raw_tg.txt')
    unique_dir = os.path.join(data_dir, 'unique_tg')
    valid_file = os.path.join(data_dir, 'validated', 'all_valid_tg.txt')

    os.makedirs(unique_dir, exist_ok=True)
    os.makedirs(os.path.dirname(valid_file), exist_ok=True)
    
    print("🚀 ЦЕХ ТЕЛЕГРАМ ЗАПУЩЕН (Метка _tg) 💋")

    # 1. Сбор
    print("📡 Собираю данные из источников...")
    ConfigFetcher(sources_file=src, output_file=raw).fetch_all()
    
    if os.path.exists(raw) and os.path.getsize(raw) > 0:
        # 2. Конвертация
        print("🛠 Конвертирую форматы...")
        FormatConverter(input_files=[raw], output_dir=unique_dir).process()
        
        # 3. Дедупликация
        print("🧼 Убираю дубликаты...")
        dedup = os.path.join(unique_dir, 'deduplicated.txt')
        if os.path.exists(dedup):
            ConfigDeduplicator(input_file=dedup, output_file=dedup).deduplicate()
            
            # 4. Валидация
            print("⚖️ Проверяю узлы на доступность...")
            ConnectivityValidator(input_file=dedup, output_file=valid_file).test_all_configs()
            
            # 5. Финальная нарезка
            print("✂️ Нарезаю сокровища по полочкам...")
            split_telegram(valid_file)
    else:
        print("📭 Новых данных в Телеграм-источниках пока нет.")

if __name__ == "__main__":
    main()
