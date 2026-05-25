import os

class ConfigDeduplicator:
    def __init__(self):
        # Путь к твоей любимой папке unique (Скриншот 1228)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.unique_dir = os.path.join(self.base_dir, 'data', 'unique')

    def _extract_core_link(self, link):
        """Умная фильтрация: выделение ядра прокси до знака '#' 
        чтобы убрать одинаковые ключи с разными именами каналов"""
        if '#' in link:
            return link.split('#')[0].strip()
        return link.strip()

    def process_file(self, file_path):
        """Очистка конкретного файла от дубликатов"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            initial_count = len(lines)
            if initial_count == 0:
                return

            seen_cores = set()
            unique_configs = []

            # Удаляем скрытые дубликаты
            for line in lines:
                cleaned = line.strip()
                if not cleaned or '://' not in cleaned:
                    continue
                
                core = self._extract_core_link(cleaned)
                if core not in seen_cores:
                    seen_cores.add(core)
                    unique_configs.append(cleaned)

            # Идеальная сортировка для красоты
            unique_configs.sort()

            # Перезаписываем этот же файл чистым результатом
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(unique_configs))

            removed = initial_count - len(unique_configs)
            filename = os.path.basename(file_path)
            print(f"[INFO] [DEDUP] Файл {filename} очищен. Удалено дублей: {removed}. Осталось: {len(unique_configs)}")

        except Exception as e:
            print(f"[ERROR] [DEDUP] Ошибка при обработке файла {os.path.basename(file_path)}: {e}")

    def process(self):
        """Поиск и очистка ВСЕХ файлов по отдельности в папке unique"""
        print("[INFO] [DEDUP] Запуск раздельной дедупликации базы данных...")
        
        if not os.path.exists(self.unique_dir):
            print(f"[INFO] [DEDUP] Папка {self.unique_dir} не найдена. Ожидание коллектора.")
            return

        try:
            files_to_process = [f for f in os.listdir(self.unique_dir) if f.endswith('.txt')]
            
            if not files_to_process:
                print("[INFO] [DEDUP] Текстовые файлы для очистки в unique не обнаружены.")
                return

            # Чистим каждый файл-протокол по отдельности!
            for filename in files_to_process:
                file_path = os.path.join(self.unique_dir, filename)
                self.process_file(file_path)
                
            print("[INFO] [DEDUP] Все раздельные файлы успешно дедуплицированы.")

        except Exception as e:
            print(f"[ERROR] [DEDUP] Критическая ошибка при сканировании папки unique: {e}")

    def deduplicate(self):
        """Интерфейс для вызова из главного скрипта main.py"""
        self.process()

if __name__ == "__main__":
    ConfigDeduplicator().process()
