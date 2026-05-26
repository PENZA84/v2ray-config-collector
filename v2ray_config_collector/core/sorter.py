import os
import json
import asyncio

class CountrySorter:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(os.path.dirname(self.script_dir))
        self.input_dir = os.path.join(self.root_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.root_dir, 'countries')
        self.max_lines = 40000 

    def write_safe(self, filepath, links):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(links))

    async def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        all_links = []
        
        # Чтение входных файлов
        if os.path.exists(self.input_dir):
            for f_name in os.listdir(self.input_dir):
                if f_name.endswith('.txt'):
                    with open(os.path.join(self.input_dir, f_name), 'r', encoding='utf-8', errors='ignore') as f:
                        all_links.extend([line.strip() for line in f if '://' in line])
        
        # Запись результата
        if all_links:
            self.write_safe(os.path.join(self.output_dir, "ALL.txt"), all_links)
            print(f"[ТАМОЖНЯ] Записано {len(all_links)} строк в ALL.txt")
        else:
            print("[ТАМОЖНЯ] Файлы не найдены или пустые!")
            
        print(f"[ТАМОЖНЯ] Обработка завершена. Результаты в: {self.output_dir}")

if __name__ == "__main__":
    asyncio.run(CountrySorter().run())
