def read_links(self):
        try:
            # Проверяем, существует ли файл источников
            if not os.path.exists(self.input_file):
                print(f"Файл {self.input_file} не найден!")
                return []

            with open(self.input_file, 'r', encoding='utf-8') as f:
                # Читаем строки, убираем лишние пробелы и комментарии
                raw_links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            seen = set()
            unique_links = []
            duplicates = []

            for link in raw_links:
                if link in seen:
                    duplicates.append(link)
                else:
                    seen.add(link)
                    unique_links.append(link)

            # Если нашли дубликаты, сохраняем их под новым именем
            if duplicates:
                # Соединяем путь: папка источника + имя duplicate_URL_sources.txt
                dup_path = os.path.join(os.path.dirname(self.input_file), 'duplicate_URL_sources.txt')
                with open(dup_path, 'w', encoding='utf-8') as f:
                    for d in duplicates:
                        f.write(d + '\n')
                print(f" Найдено дубликатов: {len(duplicates)}. Список в duplicate_URL_sources.txt")

            # Записываем статистику (проверяем, что словарь stats существует)
            if hasattr(self, 'stats') and isinstance(self.stats, dict):
                self.stats['total_links'] = len(unique_links)
            
            print(f"Уникальных ссылок для обработки: {len(unique_links)}")
            return unique_links

        except Exception as e:
            print(f"Ошибка при работе с ссылками: {e}")
            return []
