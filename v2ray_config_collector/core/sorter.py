import os
import json
import asyncio
import aiohttp

class CountrySorter:
    def __init__(self):
        # Определяем корень репозитория (на 2 уровня выше файла sorter.py)
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(os.path.dirname(self.script_dir))
        
        # Пути теперь привязаны к корню
        self.input_dir = os.path.join(self.root_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.root_dir, 'countries')
        self.cache_file = os.path.join(self.root_dir, 'ip_cache.json')
        
        self.max_lines = 40000 

    def write_safe(self, filepath, links):
        if not links: return
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        for i in range(0, len(links), self.max_lines):
            target = filepath.replace(".txt", f"_{i//self.max_lines}.txt") if i > 0 else filepath
            with open(target, 'w', encoding='utf-8') as f:
                f.write("\n".join(links[i:i + self.max_lines]))

    async def run(self):
        # Создаем папку countries, если её нет
        os.makedirs(self.output_dir, exist_ok=True)
        
        all_links = set()
        if os.path.exists(self.input_dir):
            for f_name in os.listdir(self.input_dir):
                if f_name.endswith('.txt'):
                    with open(os.path.join(self.input_dir, f_name), 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if '://' in line: all_links.add(line.strip())
        
        # ... (здесь логика сортировки, использующая self.write_safe)
        print(f"[ТАМОЖНЯ] Обработка завершена. Результаты в: {self.output_dir}")

if __name__ == "__main__":
    asyncio.run(CountrySorter().run())
