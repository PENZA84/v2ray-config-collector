import os

class ConfigDeduplicator:
    def __init__(self):
        # Пути к твоим сокровищам
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.raw_dir = os.path.join(self.base_dir, 'data', 'raw')
        
        # ОТКУДА берем (Телеграм)
        self.tg_file = os.path.join(self.raw_dir, 'telegram_configs.txt')
        
        # КУДА сохраняем (Твой основной склад)
        self.output_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')

    def process(self):
        """Чистим Телеграм и собираем всё в папку unique"""
        print(f"🧹 [DEDUP] Начинаю генерацию уникальной базы...")
        
        all_configs = []
        
        # 1. Собираем конфиги из Телеграма, если файл есть
        if os.path.exists(self.tg_file):
            try:
                with open(self.tg_file, 'r', encoding='utf-8') as f:
                    all_configs.extend(f.readlines())
                print(f"📥 Из Телеграма загружено строк: {len(all_configs)}")
            except Exception as e:
                print(f"⚠️ Ошибка чтения Телеграма: {e}")

        # 2. Можно добавить сбор из других файлов в raw, если они там есть
        # (Например, то что напарсил parser.py)

        if not all_configs:
            print("📭 Нечего чистить, исходные файлы пусты.")
            return

        # 3. Твоя фирменная чистка дублей
        initial_count = len(all_configs)
        unique_configs = sorted(list(set([c.strip() for c in all_configs if c.strip()])))
        
        # 4. Сохраняем результат в папку unique
        try:
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(unique_configs))
            
            removed = initial_count - len(unique_configs)
            print(f"✨ ОЧИСТКА ЗАВЕРШЕНА!")
            print(f"🗑 Удалено дублей: {removed}")
            print(f"💎 Сохранено в data/unique/deduplicated.txt: {len(unique_configs)}")
        except Exception as e:
            print(f"⚠️ Ошибка записи в unique: {e}")

    def deduplicate(self):
        """Для совместимости с вызовом из main.py"""
        self.process()
