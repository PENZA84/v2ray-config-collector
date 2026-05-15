import os

class ConfigDeduplicator:
    def __init__(self):
        # Пути к твоим сокровищам
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.raw_dir = os.path.join(self.base_dir, 'data', 'raw')
        # Файл, куда Телеграм-воркер складывает добычу
        self.tg_file = os.path.join(self.raw_dir, 'telegram_configs.txt')

    def process(self):
        """Удаляем дубли конкретно из телеграмных конфигов"""
        if not os.path.exists(self.tg_file):
            print("📭 Файл Телеграма пуст, дедупликация не нужна.")
            return

        print(f"🧹 [DEDUP] Начинаю чистку Телеграм-каналов от дублей...")
        
        try:
            with open(self.tg_file, 'r', encoding='utf-8') as f:
                # Читаем всё и сразу убираем дубли через set()
                configs = f.readlines()
            
            initial_count = len(configs)
            # Чистим от пробелов и оставляем только уникальные
            unique_configs = sorted(list(set([c.strip() for c in configs if c.strip()])))
            
            # Записываем обратно уже чистенькое
            with open(self.tg_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(unique_configs))
            
            removed = initial_count - len(unique_configs)
            print(f"✨ Телеграм очищен! Удалено повторов: {removed}. Осталось уникальных: {len(unique_configs)}")

        except Exception as e:
            print(f"⚠️ Ошибка при дедупликации Телеграма: {e}")

    def deduplicate(self):
        """Для совместимости с вызовом из main.py"""
        self.process()
