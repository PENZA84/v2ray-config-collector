def read_links(self):
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                # Читаем все строки, убираем пробелы и пустые
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

            # Если нашли дубли, сохраняем их в файл для тебя
            if duplicates:
                dup_path = os.path.join(os.path.dirname(self.input_file), 'duplicate_sources.txt')
                with open(dup_path, 'w', encoding='utf-8') as f:
                    for d in duplicates:
                        f.write(d + '\n')
                print(f" Найдено дубликатов: {len(duplicates)}. Список в duplicate_sources.txt")

            self.stats['total_links'] = len(unique_links)
            print(f"Уникальных ссылок для обработки: {len(unique_links)}")
            return unique_links
        except FileNotFoundError:
            print(f"Файл {self.input_file} не найден!")
            return []
